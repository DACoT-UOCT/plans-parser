import re
import os
import sys
import pyte
from loguru import logger
from datetime import datetime
from telnet_command_executor import TelnetCommandExecutor as TCE

class ExportAgent:
    def __init__(self):
        env = os.environ
        if not ('UTC_HOST' in env and 'UTC_USER' in env and 'UTC_PASS' in env):
            raise RuntimeError('Missing variables')
        self.__utc_host = env['UTC_HOST']
        self.__utc_user = env['UTC_USER']
        self.__utc_passwd = env['UTC_PASS']
        self.__read_remote_sleep = 30
        self.__read_seed_sleep = 0.35
        self.__execution_date = datetime.now()
        self.__re_ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|[0-9]|\[[0-?]*[ -/]*[@-~])|\r|\n")
        logger.warning('Using a {}s sleep call to wait for buffers from remote'.format(self.__read_remote_sleep))

    def run_full_session(self):
        logger.info('Starting FULL SESSION!')
        executor = TCE(host=self.__utc_host, logger=logger)
        logger.debug('Using TCE={}'.format(executor))
        p1outfile = self.__phase1(executor)
        juncs = self.__phase2(p1outfile)
        self.__phase3(juncs, executor)
        # self.__phase4('../../dacot-export-agent_2021-04-10T19:45:29.226290.sys_txt')
        self.__phase4(p1outfile)
        logger.info('Full session done')

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
            if idx == 10:
                break
            if idx % prog == 0:
                logger.debug('[{:05.2f}%] We are at {}'.format(100 * idx / count, junc))
            executor.command('get-seed-{}'.format(junc), 'SEED {}'.format(junc))
            executor.sleep(self.__read_seed_sleep)
            executor.read_lines(encoding="iso-8859-1")#, line_ending=b"\x1b8\x1b7")
            executor.exit_interactive_command()
            executor.command('get-timings-{}'.format(junc), 'SEED {} UPPER_TIMINGS'.format(junc))
            executor.sleep(self.__read_seed_sleep)
            executor.read_lines(encoding="iso-8859-1")#, line_ending=b"\x1b8\x1b7")
            executor.exit_interactive_command()
        self.__logout_sys(executor)
        logger.debug('Using the following phase 3 execution plan: {}'.format(executor.history()))
        executor.run(debug=True)
        self.__write_results(executor, 'utc_sys_exports/dacot-export-agent', mode='a')
        logger.info('=== PHASE 3 SESSION DONE ===')

    def __phase4(self, infile):
        screen = pyte.Screen(80, 25)
        stream = pyte.Stream(screen)
        next_token = '[get-seed'
        with open(infile, 'r') as input_data:
            lines = input_data.readlines()
            seed_start_pos = 0
            for idx, line in enumerate(lines):
                if next_token in line:
                    next_token = '[get-timings'
                    seed_start_pos = idx
                    break
            for line in lines[seed_start_pos:]:
                if next_token in line:
                    next_token = self.__swap_seed_tokens(next_token)
                    current_screen = '\n'.join(screen.display)
                    print(current_screen)
                    print('*' * 80)
                    screen.reset()
                stream.feed(line)

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
