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

    def test_control_parse_plans_timings(self):
        self.executor.reset()
        self.__login_steps(self.user, self.passwd)
        self.executor.command('LIPT A000000 TIMINGS')
        self.executor.read_lines(encoding='iso-8859-1')
        self.executor.command('ENDS')
        self.executor.run()
        results = self.executor.get_results()
        extracted_plans = results[3]
        self.assertIn('Current plan Timings', extracted_plans[2])
        self.assertIn('End of Plan Timings', extracted_plans[-1])
        plans_sample = random.sample(extracted_plans[10:-10], 100)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|[0-9]|\[[0-?]*[ -/]*[@-~])')
        for plan in plans_sample:
            if 'Plan' in plan:
                clear_plan = ansi_escape.sub('', plan)
                self.assertTrue(self.plan_parser.parse_plan(clear_plan)[0])
            elif '<BAD>' in plan:
                clear_plan = ansi_escape.sub('', plan)
                self.assertFalse(self.plan_parser.parse_plan(clear_plan)[0])
            #print('ANSI_PLAN:', bytes(plan, 'ascii'))
            clear_plan = ansi_escape.sub('', plan)
            #print('CLEAR_PLAN:', bytes(clear_plan, 'ascii'))
            self.assertTrue(self.plan_parser.parse_plan(clear_plan)[0])

    def __login_steps(self, user, passwd):
        self.executor.read_until('Username:', 15)
        self.executor.command(user)
        self.executor.read_until('Password:', 15)
        self.executor.command(passwd)
        self.executor.read_lines(encoding='iso-8859-1')
