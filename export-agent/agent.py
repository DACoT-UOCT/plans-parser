import os
import json
import argparse
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

def build_schedules(from_env=False):
    global log
    if from_env:
        log.info('Reading environment for target and credentials')
        try:
            ctrl_host = os.environ['DACOT_UOCT_CTRL_HOST']
            ctrl_user = os.environ['DACOT_UOCT_CTRL_USER']
            ctrl_pass = os.environ['DACOT_UOCT_CTRL_PASS']
        except KeyError as excep:
            log.fatal('Missing params: {}'.format(excep), exc_info=True)
            return
        log.info('Extracting data from {} with env-supplied credentials'.format(ctrl_host))
    else:
        log.info('Reading command line arguments for target and credentials')
        ctrl_host, ctrl_user, ctrl_pass = read_params()
        log.info('Extracting data from {} with command line-supplied credentials'.format(ctrl_host))
    extractor = SchedulesExtractor(ctrl_host, ctrl_user, ctrl_pass, debug=True, logger=log)
    try:
        schedules, failed = extractor.build_schedules()
    except Exception as excep:
        log.fatal('Exception ocurred in the SchedulesExtractor.build_schedules() call: {}'.format(excep), exc_info=True)
        return
    log.info('Done extracting data from control. Dumping JSON files')
    with open('schedules.json', 'w') as fp:
        json.dump(schedules, fp)
    log.info('Written {} junctions in schedules.json file'.format(len(schedules)))
    with open('failed.json', 'w') as fp:
        json.dump(failed, fp)
    log.info('Written {} failed plans, {} failed program lines for L table, {} failed program lines for S table and {} failed program lines for D table in failed.json file'
        .format(len(failed['failed_plans']), len(failed['failed_program_tables']['L']), len(failed['failed_program_tables']['S']),
        len(failed['failed_program_tables']['D'])))

def read_params():
    parser = argparse.ArgumentParser(description='Seed the mongo db')
    parser.add_argument('host', type=str, help='UOCT control system address')
    parser.add_argument('user', type=str, help='UOCT control system user name')
    parser.add_argument('passwd', type=str, help='UOCT control system user password')
    args = parser.parse_args()
    return args.host, args.user, args.passwd

if __name__ == "__main__":
    global log
    setup_logging()
    log.info('Started export agent')
    build_schedules()
