import os
import re
import random
import unittest
from dacot_parser.telnet_command_executor import TelnetCommandExecutor
from dacot_parser.utc_plan_parser import UTCPlanParser

class TestTelnetExecutorUOCT(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestTelnetExecutorUOCT, self).__init__(*args, **kwargs)
        self.host = os.environ['DACOT_UOCT_CTRL_HOST']
        self.user = os.environ['DACOT_UOCT_CTRL_USER']
        self.passwd = os.environ['DACOT_UOCT_CTRL_PASS']
        self.executor = TelnetCommandExecutor(self.host)
        self.plan_parser = UTCPlanParser()
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|[0-9]|\[[0-?]*[ -/]*[@-~])|\r|\n')

    def test_control_login_success(self):
        self.executor.reset()
        self.__login_steps(self.user, self.passwd)
        self.executor.command('ENDS')
        self.executor.run()
        results = self.executor.get_results()
        self.assertIn('Successfully logged in!', results[2][0])

    def test_control_login_invalid(self):
        self.executor.reset()
        self.__login_steps('invalid-user', 'invalid-password')
        self.executor.run()
        results = self.executor.get_results()
        self.assertIn('Access Denied', results[2][0])

    def test_control_parse_single_junction_timings(self):
        self.__helper_parse_junction_plans_timings('J001181')

    def test_control_parse_all_plans_timings(self):
        self.__helper_parse_junction_plans_timings('A000000')

    def __login_steps(self, user, passwd):
        self.executor.read_until('Username:', 15)
        self.executor.command(user)
        self.executor.read_until('Password:', 15)
        self.executor.command(passwd)
        self.executor.read_lines(encoding='iso-8859-1')

    def __helper_parse_junction_plans_timings(self, target):
        self.executor.reset()
        self.__login_steps(self.user, self.passwd)
        self.executor.command('LIPT {} TIMINGS'.format(target))
        self.executor.read_lines(encoding='iso-8859-1', line_ending=b'\x1b8\x1b7')
        self.executor.command('ENDS')
        self.executor.run()
        results = self.executor.get_results()
        extracted_plans = results[3]
        self.assertIn('Current plan Timings', extracted_plans[0])
        self.assertIn('End of Plan Timings', extracted_plans[-1])
        for plan in extracted_plans[1:-1]:
            clear_plan = self.ansi_escape.sub('', plan)
            # print(clear_plan)
            if '<BAD>' in plan:
                self.assertFalse(self.plan_parser.parse_plan(clear_plan)[0])
            else:
                self.assertTrue(self.plan_parser.parse_plan(clear_plan)[0])
