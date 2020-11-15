import json
import logging
import argparse
from mongoengine import connect
from dacot_models import PlanParseFailedMessage, Comment, User

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

def build_error_model(args):
    global log
    log.info('Reading input file: {}'.format(args.input))
    with open(args.input) as fp:
        data = json.load(fp)
    log.info('Processing {} failed plans messages'.format(len(data['failed_plans'])))
    model = PlanParseFailedMessage()
    model.plans = data['failed_plans']
    return model

def update_error_model(model):
    global log
    log.info('Updating info message in model')
    seed_user = User.objects(email='seed@dacot.uoct.cl').first()
    if not seed_user:
        log.error('Missing seed user in DB!! (seed@dacot.uoct.cl)')
        raise RuntimeError('Missing seed user in DB!! (seed@dacot.uoct.cl)')
    explain_message = 'Los siguientes planes extraídos desde el sistema de control, a través del comando LIPT, no se han logrado procesar por el modulo extractor de datos del sistema DACoT, debido a que, según la configuración actual, no son válidos. (Detalle técnico en la clase UTCPlanParser).'
    msg = Comment(author=seed_user, message=explain_message)
    model.message = msg
    model.validate()
    log.info('Done updating model')
    return model

if __name__ == "__main__":
    global log
    setup_logging()
    args = read_params()
    log.info('Args: {}'.format(args))
    connect(host=args.mongo)
    model = build_error_model(args)
    model = update_error_model(model)
    model.save()
