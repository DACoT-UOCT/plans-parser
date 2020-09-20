import os
import json
import logging
from dacot_parser import SchedulesExtractor

global log

def setup_logging():
    global log
    log_fmt = ('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%d-%b-%y %H:%M:%S')
    logging.basicConfig(format=log_fmt[0], datefmt=log_fmt[1])
    fout = logging.FileHandler('export-agent.log')
    fout.setFormatter(logging.Formatter(log_fmt[0], datefmt=log_fmt[1]))
    log = logging.getLogger('export-agent')
    log.setLevel(logging.INFO)
    log.addHandler(fout)

def build_schedules():
    global log
    log.info('Reading environment for target and credentials')
    try:
        ctrl_host = os.environ['DACOT_UOCT_CTRL_HOST']
        ctrl_user = os.environ['DACOT_UOCT_CTRL_USER']
        ctrl_pass = os.environ['DACOT_UOCT_CTRL_PASS']
    except KeyError as excep:
        log.fatal('Missing params: {}'.format(excep), exc_info=True)
        return
    log.info('Extracting data from {} with env-supplied credentials'.format(ctrl_host))
    extractor = SchedulesExtractor(ctrl_host, ctrl_user, ctrl_pass, debug=True, logger=log)
    try:
        schedules, failed = extractor.build_schedules()
    except Exception as excep:
        log.fatal('Exception ocurred in the SchedulesExtractor.build_schedules() call: {}'.format(excep), exc_info=True)
        return

if __name__ == "__main__":
    global log
    setup_logging()
    log.info('Started export agent')
    build_schedules()
