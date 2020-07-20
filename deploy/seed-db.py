import pymongo
import argparse
import json

parser = argparse.ArgumentParser(description='Seed the mongo db')
parser.add_argument('input', type=str, help='input schedules.json file')
parser.add_argument('mongo', type=str, help='mongo server url')
args = parser.parse_args()

with open(args.input, 'r') as jdf:
    jsondata = json.load(jdf)

total = len(jsondata.keys())
print('We have {} keys to upload'.format(total))

client = pymongo.MongoClient(args.mongo)
print('Getting mongo server info')
print(client.server_info())
print('Mongo OK')

i = 0
for k in jsondata:
    i += 1
    item = {
        '_id': k
    }
    p = (i / total) * 100
    item.update(jsondata[k])
    print('Inserting {} progress {:.2f}%'.format(k, p))
    try:
        result = client.db.dacot.insert_one(item)
        print('Inserted id: {}'.format(result.inserted_id))
    except pymongo.errors.DuplicateKeyError as err:
        print('Key is duplicated, deleting and retrying')
        client.db.dacot.delete_one({'_id': k})
        result = client.db.dacot.insert_one(item)
        print('Inserted id: {}'.format(result.inserted_id))

print('DONE')