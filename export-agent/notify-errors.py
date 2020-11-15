import logging
import argparse

global log

def setup_logging():
    global log
    log_fmt = ('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%d-%b-%y %H:%M:%S')
    logging.basicConfig(format=log_fmt[0], datefmt=log_fmt[1])
    log = logging.getLogger('notify-errors')
    log.setLevel(logging.INFO)

def read_params():
    parser = argparse.ArgumentParser(description='Notifies about failed parse operations on extracted plans')
    parser.add_argument('mongo', type=str, help='URL of the mongo server, including database name and credentials')
    parser.add_argument('input', type=str, help='path of the input file')
    return parser.parse_args()

if __name__ == "__main__":
    global log
    setup_logging()
    args = read_params()
    log.info('Args: {}'.format(args))