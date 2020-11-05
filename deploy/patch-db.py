import json
import jsonpatch
import logging
import argparse
from mongoengine import connect, disconnect
from pymongo.operations import ReplaceOne
from dacot_models import Junction, ChangeSet, Comment, OTU
from bson.json_util import dumps as bson_dumps
from pymongo.errors import BulkWriteError

global log

def setup_logging():
    global log
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    log = logging.getLogger('patch-db')
    log.setLevel(logging.INFO)

def setup_args():
    parser = argparse.ArgumentParser(description='Patch the productino mongo db')
    parser.add_argument('diffdb', type=str, help='database that is updated with new programs and plans data')
    parser.add_argument('proddb', type=str, help='database that contains all the production data and we want to update')
    parser.add_argument('mongo', type=str, help='mongo server url')
    return parser.parse_args()

def fast_validate_and_insert(objects, model, replace=False):
    global log
    log.info('[fast_insert]: Called with {} {} items'.format(len(objects), model.__name__))
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
            ops.append(ReplaceOne({'_id': mongo_obj.get('_id')}, mongo_obj, upsert=True))
        insert_res = model._get_collection().bulk_write(ops)
    else:
        log.info('[fast_insert]: Writing objects using insert_many')
        insert_res = model._get_collection().insert_many(mongo_objs)
    log.info('[fast_insert]: Write command done, collecting objects from remote')
    if replace:
        results = model._get_collection().find({'_id': {'$in': [x.get('_id') for x in mongo_objs]}})
    else:
        results = model._get_collection().find({'_id': {'$in': insert_res.inserted_ids}})
    mongo_objs.clear()
    for r in results:
        mongo_objs.append(model.from_json(bson_dumps(r)))
    log.info('[fast_insert]: Validating objects after bulk read')
    for obj in mongo_objs:
        obj.validate()
    log.info('[fast_insert]: Validation OK')
    log.info('[fast_insert]: Done')
    return mongo_objs

def fast_validate_and_insert_with_errors(objects, model, replace=False):
    try:
        return fast_validate_and_insert(objects, model, replace)
    except BulkWriteError as bwe:
        print(bwe.details)
        raise RuntimeError()

# ; def check_should_continue():
# ;     global log
# ;     log.warning('')
# ;     log.warning('THIS ACTION IS IRREVERSIBLE, ALL EXISTING DATA WILL BE UPDATED')
# ;     log.warning('')
# ;     log.warning('Should we continue?')
# ;     shlould_continue = input('[yes/no]: ')
# ;     if shlould_continue == 'yes':
# ;         return True
# ;     log.info('Input is not "yes". Aborting operations.')
# ;     return False

def build_junctions():
    objs = Junction.objects(version='latest').all()
    results = {}
    for junc in objs:
        dobj = junc.to_mongo().to_dict()
        mongo_id = junc.id
        del dobj['_id']
        results[dobj['jid']] = (dobj, mongo_id)
    return results

def build_otus():
    objs = OTU.objects(version='latest').all()
    results = {}
    for otu in objs:
        dobj = otu.to_mongo().to_dict()
        mongo_id = otu.id
        del dobj['_id']
        del dobj['junctions']
        results[dobj['oid']] = (dobj, mongo_id)
    return results

def build_data_from_db(args, db):
    global log
    log.info('Building data from db={}'.format(db))
    connect(db, host=args.mongo)
    juncs = build_junctions()
    otus = build_otus()
    disconnect()
    log.info('Building data from db={}. DONE'.format(db))
    return (juncs, otus)

def build_patches(new_data, current_data):
    global log
    log.info('Building patches for Junction objects')
    diff_juncs = new_data[0]
    curr_juncs = current_data[0]
    juncs_patches = []
    for jid in diff_juncs.keys():
        if jid not in curr_juncs:
            log.warning('For some reason jid={} exists in the new database, but not in the production database'.format(jid))
            continue
        patch = jsonpatch.make_patch(curr_juncs[jid][0], diff_juncs[jid][0])
        if patch:
            print(patch)
            juncs_patches.append((jid, patch, curr_juncs[jid][1]))
    log.info('Building patches for OTU objects')
    diff_otus = new_data[1]
    curr_otus = current_data[1]
    otus_patches = []
    for oid in diff_otus.keys():
        patch = jsonpatch.make_patch(curr_otus[oid][0], diff_otus[oid][0])
        if patch:
            print(patch)
            otus_patches.append((oid, patch, curr_otus[oid][1]))
    return (juncs_patches, otus_patches)

def apply_patches(current_data, patches):
    juncs = current_data[0]
    changed_juncs = []
    for junc_patch in patches[0]:
        key, patch, mongo_id = junc_patch
        new_junc = patch.apply(juncs[key][0])
        changed_juncs.append((key, mongo_id, new_junc, patch))
    otus = current_data[1]
    changed_otus = []
    for otu_patch in patches[1]:
        key, patch, mongo_id = otu_patch
        new_otu = patch.apply(otus[key][0])
        changed_otus.append((key, mongo_id, new_otu, patch))
    return (changed_juncs, changed_otus)

def save_new_data_junctions(new_data):
    junc_changesets = []
    juncs = []
    if len(new_data) == 0:
        return
    for operation in new_data:
        jid, mongo_id, new_junc, patch = operation
        juncobj = Junction.from_json(json.dumps(new_junc))
        juncobj.id = mongo_id
        change = ChangeSet(apply_to_id=jid, apply_to=juncobj, changes=patch, message='Automatic Update')
        junc_changesets.append(change)
        juncs.append(juncobj)
    fast_validate_and_insert(junc_changesets, ChangeSet)
    fast_validate_and_insert(juncs, Junction, replace=True)

def save_new_data_otus(new_data):
    changesets = []
    otus = []
    if len(new_data) == 0:
        return
    for operation in new_data:
        oid, mongo_id, new_otu, patch = operation
        otuobj = OTU.from_json(json.dumps(new_otu))
        otuobj.id = mongo_id
        change = ChangeSet(apply_to_id=oid, apply_to=otuobj, changes=patch, message='Automatic Update')
        changesets.append(change)
        otus.append(otuobj)
    fast_validate_and_insert(changesets, ChangeSet)
    fast_validate_and_insert(otus, OTU, replace=True)

def patch_db(args):
    global log
    diffdata = build_data_from_db(args, args.diffdb)
    proddata = build_data_from_db(args, args.proddb)
    patches = build_patches(diffdata, proddata)
    log.info('We have {} Junction and {} OTU patches to process'.format(len(patches[0]), len(patches[1])))
    new_data = apply_patches(proddata, patches)
    connect(args.proddb, host=args.mongo)
    save_new_data_junctions(new_data[0])
    save_new_data_otus(new_data[1])
    disconnect()

if __name__ == "__main__":
    global log
    setup_logging()
    # We have to update plans and programs for all OTUs and Junctions
    log.info('Started patch-db script v0.1')
    args = setup_args()
    patch_db(args)
    log.info('Done patching the production database [{}]'.format(args.proddb))
