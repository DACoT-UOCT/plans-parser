import os
import re
from dacot_parser.telnet_command_executor import TelnetCommandExecutor
from dacot_parser.utc_plan_parser import UTCPlanParser
from dacot_parser.utc_program_parser import UTCProgramParser

class SchedulesExtractor():
    def __init__(self, host, user, passwd):
        self.__utc_host = host
        self.__utc_user = user
        self.__utc_passwd = passwd
        self.__executor = TelnetCommandExecutor(self.__utc_host)
        self.__plans_parser = UTCPlanParser()
        self.__program_parser = UTCProgramParser()
        self.__re_ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|[0-9]|\[[0-?]*[ -/]*[@-~])|\r|\n')

    def build_schedules(self):
        self.__executor.reset()
        plans, failed_plans = self.__parse_plans('A000000')
        #week_programs, week_failed_programs = self.__parse_programs(1)
        #saturday_programs, saturday_failed_programs = self.__parse_programs(2)
        sunday_programs, sunday_failed_programs = self.__parse_programs(3)
        table_to_day = {
            1: 'L',
            2: 'S',
            3: 'D'
        }
        schedules = {}
        for idx, k in enumerate(plans.keys()):
            if idx == 3:
                break
            schedules[k] = {
                'plans': plans[k],
                'program': {
                    'L': [],
                    'S': [],
                    'D': []
                }
            }
        print('=======')
        for jk in schedules:
            for idx, k in enumerate(sunday_programs.keys()):
                day_table_code = list(sunday_programs[k].keys())[0]
                day = table_to_day[day_table_code]
                if idx == 3:
                    break
                if k[0] == 'A':
                    expanded_wildcard = k.rstrip('0')[1:]
                    if jk[1:][:len(expanded_wildcard)] == expanded_wildcard:
                        schedules[jk]['program'][day].extend(sunday_programs[k][day_table_code])
        print(schedules)
        return [], []
        #return self.__parse_plans('A000000')

    def get_results(self):
        return self.__executor.get_results()

    def __parse_programs(self, table_code):
        self.__login()
        self.__executor.command('get-programs', 'OUTT {} E'.format(table_code))
        self.__executor.read_lines(encoding='iso-8859-1', line_ending=b'\x1b8\x1b7')
        self.__logout()
        self.__executor.run()
        results = self.__executor.get_results()
        system_programs = results['get-programs'][0]
        fail = []
        programs = {}
        for program in system_programs[1:-1]:
            clean_program = self.__re_ansi_escape.sub('', program).strip()
            ok, parsed = self.__program_parser.parse_program(clean_program)
            if not ok:
                fail.append(clean_program)
            else:
                junct, hour, plan_id = parsed
                if type(hour) is list:
                    # print(clean_program, parsed) # TODO: Why?
                    continue
                if not junct in programs:
                    programs[junct] = {}
                    programs[junct][table_code] = []
                programs[junct][table_code].append([hour, plan_id])
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
        self.__executor.read_lines(encoding='iso-8859-1', line_ending=b'\x1b8\x1b7')
        self.__logout()
        self.__executor.run()
        results = self.__executor.get_results()
        system_plans = results['get-plans'][0]
        fail = []
        plans = {}
        for plan in system_plans[1:-1]:
            clean_plan = self.__re_ansi_escape.sub('', plan)
            if not '<BAD>' in clean_plan:
                ok, parsed = self.__plans_parser.parse_plan(clean_plan)
                if not ok:
                    fail.append(clean_plan)
                else:
                    junct, plan_id, plan_timings = parsed
                    if not junct in plans:
                        plans[junct] = {}
                    plans[junct][plan_id] = plan_timings
        return plans, fail
