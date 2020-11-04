import jsonpatch
import logging
import argparse
from mongoengine import connect, disconnect
from dacot_models import Junction

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
    objs = Junction.objects.all()
    results = {}
    for junc in objs:
        dobj = junc.to_mongo().to_dict()
        del dobj['_id']
        results[dobj['jid']] = dobj
    return results

def build_data_from_db(args, db):
    global log
    log.info('Building data from db={}'.format(db))
    connect(db, host=args.mongo)
    juncs = build_junctions()
    disconnect()
    log.info('Building data from db={}. DONE'.format(db))
    return (juncs, None)

def build_json_patches(new_data, current_data):
    global log
    log.info('Building patches for Junction objects')
    diff_juncs = new_data[0]
    curr_juncs = current_data[0]
    juncs_patches = []
    for jid in diff_juncs.keys():
        if jid not in curr_juncs:
            log.warning('For some reason jid={} exists in the new database, but not in the production database'.format(jid))
            continue
        patch = jsonpatch.make_patch(diff_juncs[jid], curr_juncs[jid])
        if patch:
            print(patch)
            juncs_patches.append(patch)
    print(juncs_patches)
    

def patch_db(args):
    diffdata = build_data_from_db(args, args.diffdb)
    proddata = build_data_from_db(args, args.proddb)
    patches = build_json_patches(diffdata, proddata)

if __name__ == "__main__":
    global log
    setup_logging()
    # We have to update plans and programs for all OTUs and Junctions
    log.info('Started patch-db script v0.1')
    args = setup_args()
    patch_db(args)
    log.info('Done patching the production database [{}]'.format(args.proddb))
