import re

class UTCProgramParser():
    def __init__(self):
        # [python:S4784]: There is no risk for a ReDoS since the input text to evaluate is not provided by users
        self.__re_hour = re.compile(r'(?P<hour>\d{2}:\d{2}:\d{2})\s+[A-Z]+\s+\d{3,4}\s+\(.*PLANES.*\)$')
        self.__re_plan = re.compile(r'(?P<hour>(\d{2}:\d{2}:\d{2})?)(\d{3})?\s+PLAN\s+(?P<junction>J\d{6})\s+(?P<plan>(\d+|[A-Z]{1,2}))\s+TIMETABLE$')
        self.__re_extract_hour = re.compile(r'\d{2}:\d{2}:\d{2}')

    def parse_program(self,text,hour):
        plan = self.__re_plan.match(text)
        if not plan:
            return False, None
        if plan.group('hour') != '':
            hour = [plan.group('hour')]
        return True, (plan.group('junction'), hour, plan.group('plan'))


    def parse_program_file(self, fpath, day, encoding='iso-8859-1'):
        programs = {}
        hour = '0'
        with open(fpath, encoding=encoding) as fplans:
            for line in fplans.readlines():
                line = line.strip()
                match_hour_line =  self.__re_hour.match(line)
                if match_hour_line:   
                    hour = match_hour_line.group('hour')
                ok, plan = self.parse_program(line,hour)
                if ok:
                    junct, f_hour, f_plan= plan
                    if not junct in programs:
                        programs[junct] = {}
                        if not day in programs[junct]:
                            programs[junct][day] = []
                        programs[junct][day].append([f_hour,f_plan])
        return programs