import re
import os
import csv
import time
import json
import argparse
import logging
import datetime

from concurrent.futures import ThreadPoolExecutor, as_completed
from bson.json_util import dumps as bson_dumps
from mongoengine import connect
from pymongo.operations import ReplaceOne

from dacot_models import Commune, ExternalCompany, ControllerModel

# from dacot_models import OTUProgramItem, JunctionPlan, JunctionPlanPhaseValue, Junction, JunctionMeta, OTU
# from dacot_models import ExternalCompany, UOCTUser, OTUController, ChangeSet, OTUMeta

global log

def setup_logging():
    global log
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    log = logging.getLogger('seed-db')
    log.setLevel(logging.INFO)

def fast_validate_and_insert(objects, model, replace=False):
    global log
    log.info('[fast_insert]: Validating objects before bulk write')
    mongo_objs = []
    for obj in objects:
        obj.validate()
        mongo_objs.append(obj.to_mongo())
    log.info('[fast_insert]: Validation OK')
    if replace:
        log.info('[fast_insert]: Writing objects using bulk_write')
        ops = []
        for mongo_obj in mongo_objs:
            ops.append(ReplaceOne({'_id': mongo_obj['_id']}, mongo_obj, upsert=True))
        insert_res = model._get_collection().bulk_write(ops)
    else:
        log.info('[fast_insert]: Writing objects using insert_many')
        insert_res = model._get_collection().insert_many(mongo_objs)
    log.info('[fast_insert]: Write command done, collecting objects from remote')
    mongo_objs.clear()
    if replace:
        results = model._get_collection().find({'_id': {'$in': [x['_id'] for x in mongo_objs]}})
    else:
        results = model._get_collection().find({'_id': {'$in': insert_res.inserted_ids}})
    for r in results:
        mongo_objs.append(model.from_json(bson_dumps(r)))
    log.info('[fast_insert]: Validating objects after bulk read')
    for obj in mongo_objs:
        obj.validate()
    log.info('[fast_insert]: Validation OK')
    log.info('[fast_insert]: Done')
    return mongo_objs

def setup_args():
    parser = argparse.ArgumentParser(description='Seed the mongo db')
    parser.add_argument('input', type=str, help='input schedules.json file')
    parser.add_argument('index', type=str, help='CSV index file with relevant columns')
    parser.add_argument('ctrlls_data', type=str, help='CSV data of controller models')
    parser.add_argument('mongo', type=str, help='mongo server url')
    parser.add_argument('database', type=str, help='mongo database to use')
    parser.add_argument('--rebuild', action='store_true', help='drop existing data and rebuild collections')
    parser.add_argument('--extra', action='store_true', help='build and save extra data to the remote db')
    return parser.parse_args()

def check_should_continue():
    global log
    log.warning('')
    log.warning('THIS ACTION IS IRREVERSIBLE, ALL EXISTING DATA WILL BE DEETED')
    log.warning('')
    log.warning('Should we continue?')
    shlould_continue = input('[yes/no]: ')
    if shlould_continue == 'yes':
        return True
    log.info('Input is not "yes". Aborting operations.')
    return False

def drop_old_data():
    global log
    log.info('Dropping old data')
    Commune.drop_collection()
    ExternalCompany.drop_collection()
    log.info('Done dropping data')

def read_json_data(args):
    pass

def check_csv_line_valid(line, pattern):
    if line[0] and line[1] and line[2] and pattern.match(line[3]):
        return True, line[2], line[1]
    return False, None, None

def build_csv_index_item(line):
    d = {}
    if line[6] and line[7]:
        d['commune'] = line[6].strip().upper()
        d['maintainer'] = line[7].strip().upper()
    return d

def read_csv_data(args):
    index = {}
    valid_pattern = re.compile(r'J\d{6}\-\d{8}')
    with open(args.index, 'r', encoding='utf-8-sig') as fp:
        reader = csv.reader(fp, delimiter=';')
        for line in reader:
            valid, oid, jid = check_csv_line_valid(line, valid_pattern)
            if valid:
                key = '{}.{}'.format(oid, jid)
                index[key] = build_csv_index_item(line)
    return index

def extract_company_for_commune(index_csv):
    d = {}
    for v in index_csv.values():
        if 'commune' in v and 'maintainer' in v:
            k = (v['commune'], v['maintainer'])
            if k not in d:
                d[k] = 0
            d[k] += 1
    l = []
    for k, v in d.items():
        l.append((k[0], k[1], v))
    l = sorted(l, key=lambda v: v[1])
    d = {}
    for i in l:
        if i[0] not in d:
            d[i[0]] = i[1]
    return d

def build_external_company_collection(commune_company_dict):
    s = set(commune_company_dict.values())
    d = {}
    for c in s:
        d[c] = ExternalCompany(name=c)
    for i in fast_validate_and_insert(d.values(), ExternalCompany):
        d[i.name] = i
    return d

def build_commune_collection(index_csv):
    commune_company = extract_company_for_commune(index_csv)
    companies = build_external_company_collection(commune_company)
    l = []
    for k, v in commune_company.items():
        l.append(Commune(name=k, maintainer=companies[v]))
    fast_validate_and_insert(l, Commune)

def build_controller_model_csv_item(line):
    d = {
        'company': line[0],
        'model': line[1],
        'fw': line[2],
        'check': line[3],
        'date': datetime.datetime.strptime(line[4], '%d-%m-%Y')
    }
    return d

def read_controller_models_csv(args):
    l = []
    with open(args.ctrlls_data, 'r', encoding='utf-8-sig') as fp:
        reader = csv.reader(fp, delimiter=';')
        for line in reader:
            l.append(build_controller_model_csv_item(line))
    return l

def build_controller_model_collection(models_csv):
    print(models_csv)

def rebuild(args):
    if not check_should_continue():
        return
    connect(args.database, host=args.mongo)
    drop_old_data()
    index_csv = read_csv_data(args)
    build_commune_collection(index_csv)
    controllers_model_csv = read_controller_models_csv(args)
    build_controller_model_collection(controllers_model_csv)

if __name__ == "__main__":
    global log
    setup_logging()
    log.info('Started seed-db script v0.2')
    args = setup_args()
    if args.rebuild:
        rebuild(args)
    log.info('Done Seeding the remote database')
