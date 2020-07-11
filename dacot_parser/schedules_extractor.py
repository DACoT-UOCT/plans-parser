import os
import re
from dacot_parser.telnet_command_executor import TelnetCommandExecutor
from dacot_parser.utc_plan_parser import UTCPlanParser
from dacot_parser.utc_program_parser import UTCProgramParser

class SchedulesExtractor():
    def __init__(self):
        self.__utc_host = os.environ['DACOT_UOCT_CTRL_HOST']
        self.__utc_user = os.environ['DACOT_UOCT_CTRL_USER']
        self.__utc_passwd = os.environ['DACOT_UOCT_CTRL_PASS']
        self.__executor = TelnetCommandExecutor(self.__utc_host)
        self.__plans_parser = UTCPlanParser()
        self.__program_parser = UTCProgramParser()
        self.__re_ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|[0-9]|\[[0-?]*[ -/]*[@-~])|\r|\n')

    def build_schedules(self):
        all_plans = self.__parse_plans('A000000')
        print(all_plans)

    def __login(self):
        self.__executor.read_until('Username:', 15)
        self.__executor.command(self.__utc_user)
        self.__executor.read_until('Password:', 15)
        self.__executor.command(self.__utc_passwd)
        self.__executor.read_lines(encoding='iso-8859-1')

    def __logout(self):
        self.__executor.command('ENDS')

    def __parse_plans(self, junction):
        self.__login()
        self.__executor.command('LIPT {} TIMINGS'.format(junction))
        self.__executor.read_lines(encoding='iso-8859-1', line_ending=b'\x1b8\x1b7')
        self.__logout()
        self.__executor.run()
        res = self.__executor.get_results()
        fail = []
        plans = {}
        for plan in res[id][1:-1]: #TODO: FIX THIS
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
