import re
import os
import csv
import time
import json
import argparse
import logging

from concurrent.futures import ThreadPoolExecutor, as_completed
from bson.json_util import dumps as bson_dumps
from mongoengine import connect
from pymongo.operations import ReplaceOne

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
    parser.add_argument('mongo', type=str, help='mongo server url')
    parser.add_argument('database', type=str, help='mongo database to use')
    parser.add_argument('--rebuild', action='store_true', help='drop existing data and rebuild collections')
    parser.add_argument('--extra', action='store_true', help='build and save extra data to the remote db')
    return parser.parse_args()

if __name__ == "__main__":
    global log
    setup_logging()
    log.info('Started seed-db script')
    args = setup_args()
    print(args)
    log.info('Done Seeding the remote database')
