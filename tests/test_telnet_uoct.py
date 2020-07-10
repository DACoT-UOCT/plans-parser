import os
import unittest
from dacot_parser.telnet_command_executor import TelnetCommandExecutor

class TestTelnetExecutorUOCT(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestTelnetExecutorUOCT, self).__init__(*args, **kwargs)
        self.host = os.environ['DACOT_UOCT_CTRL_HOST']
        self.user = os.environ['DACOT_UOCT_CTRL_USER']
        self.passwd = os.environ['DACOT_UOCT_CTRL_PASS']
        self.executor = TelnetCommandExecutor(self.host)

    def __test_control_login_success(self):
        self.executor.reset()
        self.executor.read_until('Username:', 15)
        self.executor.command(self.user)
        self.executor.read_until('Password:', 15)
        self.executor.command(self.passwd)
        self.executor.read_lines()
        self.executor.run()
        results = self.executor.get_results()
        print(results)

    def test_control_login_invalid(self):
        self.executor.reset()
        self.executor.read_until('Username:', 15)
        self.executor.command('invalid-username')
        self.executor.read_until('Password:', 15)
        self.executor.command('invalid-password')
        self.executor.read_lines()
        self.executor.run()
        results = self.executor.get_results()
        self.assertIn('Access Denied', results[2][0])