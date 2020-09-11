import pymongo
import argparse
import json
import logging
from dacot_models import OTUProgramItem

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
log = logging.getLogger('seed-db')
log.setLevel(logging.INFO)

parser = argparse.ArgumentParser(description='Seed the mongo db')
parser.add_argument('input', type=str, help='input schedules.json file')
parser.add_argument('mongo', type=str, help='mongo server url')
args = parser.parse_args()

with open(args.input, 'r') as jdf:
    jsondata = json.load(jdf)

total = len(jsondata.keys())
log.info('We have {} keys to upload'.format(total))

client = pymongo.MongoClient(args.mongo)
log.info('Getting mongo server info')
log.info(client.server_info())
log.info('Mongo OK')
log.info('Building models')

i = 0
for k, v in jsondata.items():
    p = (i / total) * 100
    log.info('Inserting {} progress {:.2f}%'.format(k, p))
    programs = []
    i += 1
    for day, items in v['program'].items():
        for item in items:
            programs.append(OTUProgramItem(day=day, time=item[0][:5], plan=item[1]))
    break


# i = 0
# for k in jsondata:
#     i += 1
#     item = {
#         '_id': k
#     }
#     p = (i / total) * 100
#     item.update(jsondata[k])
#     print('Inserting {} progress {:.2f}%'.format(k, p))
#     try:
#         result = client.dacot.junction.insert_one(item)
#         print('Inserted id: {}'.format(result.inserted_id))
#     except pymongo.errors.DuplicateKeyError as err:
#         print('Key is duplicated, deleting and retrying')
#         client.dacot.junction.delete_one({'_id': k})
#         result = client.dacot.junction.insert_one(item)
#         print('Inserted id: {}'.format(result.inserted_id))
# 
# print('DONE')