import os
import unittest
from parser.utc_plan_parser import UTCPlanParser

class TestPlanParser(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestPlanParser, self).__init__(*args, **kwargs)
        self.parser = UTCPlanParser()
        self.input = os.path.join(os.path.dirname(__file__), 'plans.txt')

    def test_parse_file(self):
        plans = self.parser.parse_plans_file(self.input)
        self.assertEqual(len(plans.keys()), 4)
    