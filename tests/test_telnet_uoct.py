import os
import unittest
from dacot_parser.schedules_extractor import SchedulesExtractor

class TestTelnetExecutorUOCT(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestTelnetExecutorUOCT, self).__init__(*args, **kwargs)
        #self.invalid_login_extractor = SchedulesExtractor(ctrl_host, 'invalid-user', 'invalid-pass')

    def test_build_schedules(self):
        try:
            ctrl_host = os.environ['DACOT_UOCT_CTRL_HOST']
            ctrl_user = os.environ['DACOT_UOCT_CTRL_USER']
            ctrl_pass = os.environ['DACOT_UOCT_CTRL_PASS']
        except KeyError:
            self.skipTest('missing env variables')
        correct_extractor = SchedulesExtractor(ctrl_host, ctrl_user, ctrl_pass)
        schedules = correct_extractor.build_schedules()
        self.assertListEqual([], schedules[1], 'found invalid plans')

#    def test_invalid_login(self):
#        pass
