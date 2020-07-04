import unittest
from parser.utc_plan_parser import UTCPlanParser

class TestPlanParser(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestPlanParser, self).__init__(*args, **kwargs)
        self.parser = UTCPlanParser()

    def test_example(self):
        self.assertEqual(1, 1)
    