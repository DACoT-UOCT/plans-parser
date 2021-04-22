import re
import os
import sys
import pyte
import pandas as pd
from loguru import logger
import dacot_models as dm
from datetime import datetime
from gql import gql, Client
from gql_query_builder import GqlQuery
from gql.transport.aiohttp import AIOHTTPTransport
from telnet_command_executor import TelnetCommandExecutor as TCE

class ExportAgent:
    def __init__(self):
        env = os.environ
        if not ('UTC_HOST' in env and 'UTC_USER' in env and 'UTC_PASS' in env and 'BACKEND_URL' in env):
            raise RuntimeError('Missing variables')
        self.__utc_host = env['UTC_HOST']
        self.__utc_user = env['UTC_USER']
        self.__utc_passwd = env['UTC_PASS']
        self.__backend = env['BACKEND_URL']
        self.__read_remote_sleep = 30
        self.__read_seed_sleep = 0.35
        self.__execution_date = datetime.now()
        self.__re_ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|[0-9]|\[[0-?]*[ -/]*[@-~])|\r|\n")
        self.__re_ctrl_type = re.compile(r'Controller Type\s+:\s\[(?P<ctrl_type>.*)\]')
        self.__re_intergreens_table = re.compile(r'\s(?P<phase_name>[A-Z])\s+(?P<is_demand>N|Y)\s+(?P<min_time>\d+)\s+(?P<max_time>\d+)\s+(?P<intergreens>((X|\d+)\s+)+(X|\d+))')
        self.__re_plan = re.compile(r'^Plan\s+(?P<id>\d+)\s(?P<junction>J\d{6}).*(?P<cycle>CY\d{3})\s(?P<phases>[A-Z0-9\s,!\*]+)$')
        self.__re_extract_phases = re.compile(r"\s[A-Z]\s\d+")
        self.__re_extract_sequence = re.compile(r'Cyclic Check Sequence\s+:\s\[(?P<sequence>[A-Z]+)')
        self.__re_program_hour = re.compile(r"(?P<hour>\d{2}:\d{2}:\d{2}).*$")
        self.__re_program = re.compile(r"(?P<hour>(\d{2}:\d{2}:\d{2})?)(\d{3})?\s+PLAN\s+(?P<junction>[J|A]\d{6})\s+(?P<plan>(\d+|[A-Z]{1,2}))\s+TIMETABLE$")
        transport = AIOHTTPTransport(url=self.__backend)
        self.__api = Client(transport=transport, fetch_schema_from_transport=True)
        logger.warning('Using a {}s sleep call to wait for buffers from remote'.format(self.__read_remote_sleep))
        logger.info('Using {} as API Endpoint'.format(self.__backend))

    def run_full_session(self):
        logger.info('Starting FULL SESSION!')
        executor = TCE(host=self.__utc_host, logger=logger)
        logger.debug('Using TCE={}'.format(executor))
        p1outfile = self.__phase1(executor)
        juncs = self.__phase2(p1outfile)
        self.__phase3(juncs, executor)
        self.__phase4(p1outfile)
        # p1outfile = '../../DACOT_EXPORT_FULL_OK'
        results = self.__phase4(p1outfile)
        self.__phase5(p1outfile, results)
        self.__phase6(p1outfile, results)
        models = self.__build_models(results)
        self.__upload_models(models)
        logger.info('Full session done')

    def __upload_models(self, models):
        # TODO: Optimization: maybe in parallel
        programs, sequences, inter, plan = models
        for k, v in programs.items():
            state = self.__get_project(k)
            if state == 0:
                self.__create_project(k, models)

    def __generate_junc_ids(self, oid):
        base = 'J{}'.format(oid[1:-1])
        for i in range(1, 10):
            yield base + str(i)

    def __create_project(self, k, models):
        logger.info('Creating project {}'.format(k))
        current_oid = '"{}"'.format(k)
        metadata = GqlQuery().fields(['maintainer: "SpeeDevs"', 'commune: 0']).query('', alias='metadata').generate()
        model = GqlQuery().fields(['company: "SpeeDevs"', 'model: "Default"', 'firmwareVersion: "Missing Value"', 'checksum: "Missing Value"']).query('', alias='model').generate()
        controller = GqlQuery().fields([model, 'gps: false', 'addressReference: ""']).query('', alias='controller').generate()
        default_junc_meta = GqlQuery().fields(['coordinates: [0, 0]', 'addressReference: ""']).query('', alias='metadata').generate()
        junctions = []
        for juncid in self.__generate_junc_ids(k):
            if juncid in models[3]:
                junc = GqlQuery().fields(['jid: "{}"'.format(juncid), default_junc_meta]).generate()
                junctions.append(junc)
            else:
                break
        otu = GqlQuery().fields(['junctions: {}'.format(junctions).replace("'{", '{').replace("}'", '}')]).query('', alias='otu').generate()
        details = GqlQuery().fields([
            'oid: {}'.format(current_oid),
            metadata,
            otu,
            controller,
            'observation: "Created from DACoTExportAgent"'
        ]).generate()
        mutation = GqlQuery().query('createProject', input={'projectDetails': details}).operation('mutation').fields(['oid']).generate()
        try:
            self.__api.execute(gql(mutation))
            logger.debug('Project {} created in NEW status'.format(k))
        except Exception as ex:
            # TODO: Check for E11000 code (duplicate can be ignored)
            logger.error('Failed to create project for {}. Cause: {}'.format(k, ex)) # FIXME: Send to backend

    def __get_project(self, k):
        # 0 = Create NEW
        # 1 = Update NEW
        # 2 = Update PRODUCTION
        logger.debug('Getting data for {} in PRODUCTION status'.format(k))
        qry = GqlQuery().fields(['id']).query('project', input={'oid': '"{}"'.format(k), 'status': '"PRODUCTION"'}).operation('query').generate()
        res = self.__api.execute(gql(qry))
        if res['project']:
            return 2
        else:
            logger.debug('Getting data for {} in NEW status'.format(k))
            qry = GqlQuery().fields(['id']).query('project', input={'oid': '"{}"'.format(k), 'status': '"NEW"'}).operation('query').generate()
            res = self.__api.execute(gql(qry))
            if res['project']:
                return 1
            else:
                return 0

    def __build_models(self, results):
        table_id_to_day = {
            1: 'L',
            2: 'S',
            3: 'D'
        }
        programs = {}
        sequences = {}
        plan = {}
        inter = {}
        for k, v in results.items():
            oid = 'X{}0'.format(k[1:-1])
            plans = []
            for p in v['plans']:
                start = []
                for s in p[2]:
                    val = dm.JunctionPlanPhaseValue(phid=s[0], value=s[1])
                    val.validate()
                    start.append(val)
                newp = dm.JunctionPlan(plid=p[0], cycle=p[1], system_start=start)
                newp.validate()
                plans.append(newp)
            plan[k] = plans
            if oid not in programs and v['program']:
                progs = []
                for p in v['program']:
                    newp = dm.OTUProgramItem(day=table_id_to_day[p[0]], time=p[1], plan=p[2])
                    newp.validate()
                    progs.append(newp)
                programs[oid] = progs
            if oid not in sequences and v['sequence']:
                seqs = []
                for seq in v['sequence']:
                    news = dm.OTUSequenceItem(seqid=seq)
                    news.validate()
                    seqs.append(news)
                sequences[oid] = seqs
            inters = []
            if isinstance(v['intergreens'], pd.DataFrame):
                inter_cols = v['intergreens'].columns[3:]
                for i in inter_cols:
                    for j in inter_cols:
                        if i != j:
                            newi = dm.OTUIntergreenValue(phfrom=i, phto=j, value=v['intergreens'][i][j])
                            newi.validate()
                            inters.append(newi)
            inter[k] = inters
        return programs, sequences, inter, plan

    def __phase1(self, executor):
        self.__login_sys(executor)
        self.__get_plans(executor)
        self.__get_programs(executor)
        self.__logout_sys(executor)
        logger.debug('Using the following phase 1 execution plan: {}'.format(executor.history()))
        logger.info('=== STARTING PHASE 1 SESSION EXECUTION ===')
        executor.run(debug=True)
        outfile = self.__write_results(executor, 'utc_sys_exports/dacot-export-agent')
        logger.info('=== PHASE 1 SESSION DONE ===')
        return outfile

    def __phase2(self, infile):
        logger.info('=== STARTING PHASE 2 SESSION EXECUTION ===')
        all_junctions = set()
        count = 0
        with open(infile, 'r') as input_data:
            auth_ok = False
            for line in input_data:
                count += 1
                if 'Successfully logged in!' in line:
                    auth_ok = True
                if '[get-plans-wildcard]' in line:
                    if not auth_ok:
                        raise ValueError('Invalid export file, could not login to UTC')
                    else:
                        break
            for line in input_data:
                count += 1
                clean_line = self.__re_ansi_escape.sub('', line).strip()
                if 'End of Plan Timings' in clean_line:
                    break
                if clean_line:
                    junc = clean_line[0:20].split()[2]
                    all_junctions.add(junc)
        logger.debug('Parsed {} lines, got {} unique JIDs'.format(count, len(all_junctions)))
        logger.info('=== PHASE 2 SESSION DONE ===')
        return all_junctions

    def __phase3(self, juncs, executor):
        logger.info('=== STARTING PHASE 3 SESSION EXECUTION ===')
        count = len(juncs)
        prog = int(count / 20)
        logger.info('Building UPPER_TIMINGS and SEED data commands for {} Junctions'.format(count))
        executor.reset()
        self.__login_sys(executor)
        for idx, junc in enumerate(juncs):
            idx = idx + 1
            if idx % prog == 0:
                logger.debug('[{:05.2f}%] We are at {}'.format(100 * idx / count, junc))
                break # TODO: FIXME: Remove this in final version
            self.__get_seed_data(executor, junc)
        self.__logout_sys(executor)
        logger.debug('Using the following phase 3 execution plan: {}'.format(executor.history()))
        executor.run(debug=True)
        self.__write_results(executor, 'utc_sys_exports/dacot-export-agent', mode='a')
        logger.info('=== PHASE 3 SESSION DONE ===')

    def __get_seed_data(self, executor, junc):
        executor.command('get-seed-{}'.format(junc), 'SEED {}'.format(junc))
        executor.sleep(self.__read_seed_sleep)
        executor.read_until_min_bytes(2000, encoding="iso-8859-1", line_ending=b"\x1b8\x1b7")
        executor.exit_interactive_command()
        executor.command('get-timings-{}'.format(junc), 'SEED {} UPPER_TIMINGS'.format(junc))
        executor.sleep(self.__read_seed_sleep)
        executor.read_until_min_bytes(2000, encoding="iso-8859-1", line_ending=b"\x1b8\x1b7")
        executor.exit_interactive_command()

    def __phase4(self, infile):
        logger.info('=== STARTING PHASE 4 SESSION EXECUTION ===')
        screen = pyte.Screen(80, 25)
        stream = pyte.Stream(screen)
        results = {}
        next_token = '[get-seed'
        with open(infile, 'r') as input_data:
            lines = input_data.readlines()
            seed_start_pos = 0
            current_junc = ''
            for idx, line in enumerate(lines):
                if next_token in line:
                    current_junc = line.split('-')[2].split(']')[0]
                    next_token = '[get-timings'
                    seed_start_pos = idx
                    break
            count = len(lines) - seed_start_pos
            step = count / 20
            for idx, line in enumerate(lines[seed_start_pos:]):
                if next_token in line:
                    next_token = self.__swap_seed_tokens(next_token)
                    current_screen = '\n'.join(screen.display)
                    if not current_junc in results:
                        results[current_junc] = self.__create_entry()
                    self.__extract_data_from_screen(current_screen, next_token, current_junc, results)
                    screen.reset()
                    current_junc = line.split('-')[2].split(']')[0]
                if idx % step == 0:
                    logger.debug('[{:05.2f}%] We are at {}'.format(100 * idx / count, current_junc))
                stream.feed(line)
            current_screen = '\n'.join(screen.display)
            self.__extract_data_from_screen(current_screen, next_token, current_junc, results)
            screen.reset()
        logger.info('=== PHASE 4 SESSION DONE ===')
        return results

    def __phase5(self, infile, results):
        logger.info('=== STARTING PHASE 5 SESSION EXECUTION ===')
        failed_plans = [] # FIXME: Send to backend
        with open(infile, 'r') as input_data:
            for line in input_data:
                clean_line = self.__re_ansi_escape.sub('', line).strip()
                if clean_line:
                    if 'End of Plan Timings' in clean_line:
                        break
                    match = self.__re_plan.match(clean_line)
                    if match:
                        self.__build_single_plan(match, results)
                    else:
                        failed_plans.append(clean_line)
        logger.info('=== PHASE 5 SESSION DONE ===')

    def __phase6(self, infile, results):
        logger.info('=== STARTING PHASE 6 SESSION EXECUTION ===')
        failed_programs = [] # FIXME: Send to backend
        parsed_programs = []
        with open(infile, 'r') as input_data:
            lines = input_data.readlines()
            program_start = 0
            for idx, line in enumerate(lines):
                if 'End of Plan Timings' in line:
                    program_start = idx + 1
                    break
            current_table = -1
            current_hour = ''
            for line in lines[program_start:]:
                clean_line = self.__re_ansi_escape.sub('', line).strip()
                if clean_line:
                    if '[end-session]' in clean_line:
                        break
                    if 'Timetable' in clean_line and 'Title:-' in clean_line:
                        current_table = int(re.match(r'.*Timetable\s(\d+).*', clean_line).group(1))
                    match_hour_line = self.__re_program_hour.match(clean_line)
                    if match_hour_line:
                        current_hour = match_hour_line.group("hour")[:-3]
                    match = self.__re_program.match(clean_line)
                    if match:
                        if ':' in match.group('hour'):
                            current_hour = match.group("hour")[:-3]
                        parsed_programs.append((current_table, current_hour, match.group('junction'), match.group('plan')))
                    else:
                        failed_programs.append(clean_line)
        self.__expand_wildcards(parsed_programs, results)
        logger.info('=== PHASE 6 SESSION DONE ===')

    def __expand_wildcards(self, programs, results):
        for p in programs:
            if p[2][0] == 'A':
                for possible in self.__wildcard_generator(p[2]):
                    if possible in results:
                        new_prog = (p[0], p[1], p[3])
                        results[possible]['program'].append(new_prog)
            else:
                if not p[2] in results:
                    results[p[2]] = self.__create_entry()
                    logger.warning('{} not in results. Creating entry.'.format(p[2])) # FIXME: Send to backend
                new_prog = (p[0], p[1], p[3])
                results[p[2]]['program'].append(new_prog)

    def __wildcard_generator(self, wildcard):
        pattern = wildcard.rstrip("0")[1:]
        lendiff = 6 - len(pattern)
        limit = 10 ** lendiff
        n = 0
        formatstr = "J{}{:0" + str(lendiff) + "d}"
        while n < limit:
            yield formatstr.format(pattern, n)
            n += 1

    def __create_entry(self):
        return {
            'ctrl_type': None,
            'intergreens': None,
            'plans': [],
            'program': [],
            'sequence': None
        }

    def __build_single_plan(self, match, results):
        plan_id = match.group('id')
        junc = match.group('junction')
        cycle = match.group('cycle')
        for_re = ' ' + match.group("phases")
        phases = []
        for x in self.__re_extract_phases.findall(for_re):
            name, start = x.strip().split()
            phases.append((str(ord(name) - 64), str(int(start))))
        cycle_int = int(cycle.split('CY')[1])
        item = (plan_id, cycle_int, phases)
        if junc not in results:
            results[junc] = self.__create_entry()
            logger.warning('{} not in results. Creating entry.'.format(junc)) # FIXME: Send to backend
        results[junc]['plans'].append(item)

    def __extract_data_from_screen(self, screen, token, junc, results):
        if 'seed' in token:
            sequence_match = list(self.__re_extract_sequence.finditer(screen, re.MULTILINE))
            if len(sequence_match) != 1:
                logger.warning('Failed to find Sequence for {}'.format(junc)) # FIXME: Send to backend
            else:
                seqstr = sequence_match[0].group('sequence').strip()
                seq = []
                for pid in seqstr:
                    seq.append(str(ord(pid) - 64))
                results[junc]['sequence'] = seq
            ctrl_match = list(self.__re_ctrl_type.finditer(screen, re.MULTILINE))
            if len(ctrl_match) != 1:
                logger.warning('Failed to find ControllerType for {}'.format(junc))
                return # FIXME: Send to backend
            results[junc]['ctrl_type'] = ctrl_match[0].group('ctrl_type').strip()
        elif 'timings' in token:
            rows_match = list(self.__re_intergreens_table.finditer(screen, re.MULTILINE))
            if len(rows_match) == 0:
                logger.warning('Failed to get IntergreensData for {}'.format(junc))
                return # FIXME: Send to backend
            table = []
            names = []
            for row in rows_match:
                inter_values = row.group('intergreens')
                names.append(row.group('phase_name'))
                trow = [row.group('phase_name'), row.group('is_demand'), row.group('min_time'), row.group('max_time')]
                trow.extend(inter_values.split())
                table.append(trow)
            column_names = ['Phase', 'IsDemand', 'MinTime', 'MaxTime']
            column_names.extend(names)
            df = pd.DataFrame(table, columns=column_names)
            df = df.set_index('Phase')
            results[junc]['intergreens'] = df

    def __swap_seed_tokens(self, token):
        if 'seed' in token:
            next_token = '[get-timings'
        else:
            next_token = '[get-seed'
        return next_token

    def __get_programs(self, executor):
        logger.info('Building get-programs procedure')
        for day_table_code in range(1, 4):
            executor.command('get-programs-{}'.format(day_table_code), 'OUTT {} E'.format(day_table_code))
            executor.sleep(self.__read_remote_sleep)
            executor.read_lines(encoding="iso-8859-1", line_ending=b"\x1b8\x1b7")
        logger.debug('Get-Programs built')

    def __write_results(self, executor, output_prefix, mode='w'):
        outfile = './{}_{}.sys_txt'.format(output_prefix, self.__execution_date.isoformat())
        logger.info('Saving TCE execution result to {}'.format(outfile))
        with open(outfile, mode) as out:
            res = executor.get_results()
            for k, v in res.items():
                out.write('[{}] {}\n'.format(k, '=' * 5))
                for possible_list in v:
                    if type(possible_list) == list:
                        for line in possible_list:
                            out.write('{}\n'.format(line))
                    else:
                        out.write('{}\n'.format(possible_list))
        logger.info('Saving done in {}'.format(outfile))
        return outfile

    def __get_plans(self, executor):
        logger.info('Building get-plans procedure')
        executor.command('get-plans-wildcard', 'LIPT A000000 TIMINGS')
        executor.sleep(self.__read_remote_sleep)
        executor.read_lines(encoding="iso-8859-1", line_ending=b"\x1b8\x1b7")
        logger.debug('Get-Plans built')

    def __login_sys(self, executor):
        logger.info('Building login procedure')
        executor.read_until('Username:', 15)
        executor.command('login-user', self.__utc_user)
        executor.read_until('Password:', 15)
        executor.command('login-pass', self.__utc_passwd)
        executor.read_lines(encoding='iso-8859-1')
        logger.debug('Login built')

    def __logout_sys(self, executor):
        logger.info('Building logout procedure')
        executor.command("end-session", "ENDS")
        logger.debug('Logout built')

if __name__ == '__main__':
    logger.remove()
    logger.add(sys.stderr, level='DEBUG')
    try:
        logger.info('Starting')
        agent = ExportAgent()
        agent.run_full_session()
        logger.info('Done')
    except Exception as excep:
        logger.exception('Global Exception!')
