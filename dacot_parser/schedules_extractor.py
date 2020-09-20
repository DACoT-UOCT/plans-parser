import os
import re
from dacot_parser.telnet_command_executor import TelnetCommandExecutor
from dacot_parser.utc_plan_parser import UTCPlanParser
from dacot_parser.utc_program_parser import UTCProgramParser

class SchedulesExtractor():
    def __init__(self, host, user, passwd, debug=False, logger=None):
        self.__logger = logger
        self.__utc_user = user
        self.__utc_passwd = passwd
        self.__executor = TelnetCommandExecutor(host, logger=self.__logger)
        self.__plans_parser = UTCPlanParser()
        self.__program_parser = UTCProgramParser()
        self.__re_ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|[0-9]|\[[0-?]*[ -/]*[@-~])|\r|\n')
        self.__debug_enabled = debug

    def __log_print(self, msg):
        if self.__logger:
            self.__logger.info(msg)
        else:
            print(msg)

    def build_schedules(self):
        self.__log_print('Resetting the TelnetCommandExecutor instance')
        self.__executor.reset()
        plans, failed_plans = self.__parse_plans('A000000')
        week_programs, failed_week_programs = self.__parse_programs(1)
        saturday_programs, failed_saturday_programs = self.__parse_programs(2)
        sunday_programs, failed_sunday_programs = self.__parse_programs(3)
        schedules = self.__build_schedules_dict(plans)
        schedules = self.__add_plans_to_schedules(plans, schedules)
        schedules = self.__add_programs_to_schedules(week_programs, 'L', schedules)
        schedules = self.__add_programs_to_schedules(saturday_programs, 'S', schedules)
        schedules = self.__add_programs_to_schedules(sunday_programs, 'D', schedules)
        return schedules, [failed_plans, failed_week_programs, failed_saturday_programs, failed_sunday_programs]

    def __build_schedules_dict(self, junctions):
        schedules = {}
        for j in junctions:
            schedules[j] = {
                'plans': None,
                'program': {
                    'L': [],
                    'S': [],
                    'D': [],
                }
            }
        return schedules

    def __add_plans_to_schedules(self, plans, schedules):
        for p in plans:
            schedules[p]['plans'] = plans[p]
        return schedules

    def __add_programs_to_schedules(self, programs, day, schedules):
        for p in programs:
            if p[0][0] == 'A':
                for possible in self.__expand_wildcard(p[0]):
                    if possible in schedules:
                        schedules[possible]['program'][day].append([p[1], p[2]])
            elif p[0] in schedules:
                schedules[p[0]]['program'][day].append([p[1], p[2]])
            else:
                if self.__debug_enabled:
                    self.__log_print('{} is not in schedules (no plans for this junction?) day: {} parsed: {}'.format(p[0], day, p))
        return schedules

    def __expand_wildcard(self, wildcard):
        pattern = wildcard.rstrip('0')[1:]
        lendiff = (6 - len(pattern))
        limit = 10 ** lendiff
        n = 0
        formatstr = 'J{}{:0' + str(lendiff) + 'd}'
        while n < limit:
            yield formatstr.format(pattern, n)
            n += 1

    def get_results(self):
        return self.__executor.get_results()

    def __parse_programs(self, table_code):
        self.__login()
        self.__executor.command('get-programs', 'OUTT {} E'.format(table_code))
        self.__executor.sleep(40)
        self.__executor.read_lines(encoding='iso-8859-1', line_ending=b'\x1b8\x1b7')
        self.__logout()
        self.__executor.run(self.__debug_enabled)
        results = self.__executor.get_results()
        system_programs = results['get-programs'][0][1:-1]
        fail = []
        programs = []
        for program in system_programs:
            clean_program = self.__re_ansi_escape.sub('', program).strip()
            ok, parsed = self.__program_parser.parse_program(clean_program)
            if not ok:
                fail.append(clean_program)
            else:
                programs.append(parsed)
        if self.__debug_enabled:
            self.__log_print('From a total of {} plans, we parsed {} and {} have problems'.format(len(system_programs), len(programs), len(fail)))
        return programs, fail

    # TODO: Check the case when there is no slots available in the system
    def __login(self):
        self.__executor.read_until('Username:', 15)
        self.__executor.command('login-user', self.__utc_user)
        self.__executor.read_until('Password:', 15)
        self.__executor.command('login-pass', self.__utc_passwd)
        self.__executor.read_lines(encoding='iso-8859-1')

    def __logout(self):
        self.__executor.command('end-session', 'ENDS')

    def __parse_plans(self, junction):
        self.__login()
        self.__executor.command('get-plans', 'LIPT {} TIMINGS'.format(junction))
        self.__executor.sleep(40)
        self.__executor.read_lines(encoding='iso-8859-1', line_ending=b'\x1b8\x1b7')
        self.__logout()
        self.__executor.run(self.__debug_enabled)
        results = self.__executor.get_results()
        system_plans = results['get-plans'][0][1:-1]
        fail = []
        ignored, success = 0, 0
        plans = {}
        for plan in system_plans:
            clean_plan = self.__re_ansi_escape.sub('', plan)
            if '<BAD>' in clean_plan:
                ignored += 1
                continue
            ok, parsed = self.__plans_parser.parse_plan(clean_plan)
            if not ok:
                fail.append(clean_plan)
                if self.__debug_enabled:
                    self.__log_print('PARSE FAILED: {}'.format(bytes(clean_plan, 'ascii')))
            else:
                success += 1
                junct, plan_id, plan_timings = parsed
                if not junct in plans:
                    plans[junct] = {}
                plans[junct][plan_id] = plan_timings
        if self.__debug_enabled:
            self.__log_print('From a total of {} plans, we parsed {}, {} have problems and {} were ignored'.format(len(system_plans), success, len(fail), ignored))
        return plans, fail
