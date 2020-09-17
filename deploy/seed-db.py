import re
import os
import csv
import argparse
import json
import logging

from mongoengine import connect

from dacot_models import OTUProgramItem, JunctionPlan, JunctionPlanPhaseValue, Junction, JunctionMeta, OTU
from dacot_models import ExternalCompany, UOCTUser, OTUController, ChangeSet, OTUMeta

global log

def setup_logging():
    global log
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    log = logging.getLogger('seed-db')
    log.setLevel(logging.INFO)

def setup_args():
    parser = argparse.ArgumentParser(description='Seed the mongo db')
    parser.add_argument('input', type=str, help='input schedules.json file')
    parser.add_argument('index', type=str, help='CSV index file with relevant columns')
    parser.add_argument('mongo', type=str, help='mongo server url')
    return parser.parse_args()

def drop_data():
    global log
    log.info('¡¡¡¡DROPPING OLD DATA!!!!')
    Junction.drop_collection()
    OTU.drop_collection()
    ExternalCompany.drop_collection()
    UOCTUser.drop_collection()
    OTUController.drop_collection()
    ChangeSet.drop_collection()
    log.info('Done dropping old collections')

def phase1(jsdata):
    global log
    log.info('=' * 60)
    log.info('Phase 1. Creating initial objects')
    log.info('=' * 60)
    log.info('Building models from JSON file')
    seed_user = UOCTUser(uid=1, full_name='DACoT Automated DB Seeder', email='dacot@santiago.uoct.cl', area='TIC', rut='00000000-0')
    seed_user = seed_user.save().reload()
    junctions = []
    otus = {}
    total = len(jsdata)
    i = 0
    for k, v in jsdata.items():
        i += 1
        p = (i / total) * 100
        log.info('Building model for {} progress {:.2f}%'.format(k, p))
        plans = []
        oid = 'X' + k[1:-1] + '0'
        if not oid in otus:
            programs = []
            for day, items in v['program'].items():
                for item in items:
                    programs.append(OTUProgramItem(day=day, time=item[0][:5], plan=item[1]))
            metadata = OTUMeta(version='base', status='SYSTEM', status_user=seed_user)
            otus[oid] = OTU(oid=oid, program=programs, metadata=metadata)
        for plid, plan in v['plans'].items():
            system_start = []
            for phid, phvalue in plan['system_start'].items():
                system_start.append(JunctionPlanPhaseValue(phid=phid, value=phvalue))
            plans.append(JunctionPlan(plid=plid, cycle=plan['cycle'], system_start=system_start))
        junctions.append(Junction(jid=k, plans=plans, metadata=JunctionMeta()))
    log.info('Bulk inserting {} junctions, this can take a while...'.format(len(junctions)))
    junctions = Junction.objects.insert(junctions)
    log.info('Done inserting junctions')
    log.info('Updatig OTUs with junctions references')
    i = 0
    for j in junctions:
        i += 1
        p = (i / total) * 100
        oid = 'X' + j['jid'][1:-1] + '0'
        log.info('Updating model for {} progress {:.2f}%'.format(oid, p))
        otus[oid].junctions.append(j)
    otus = otus.values()
    log.info('Bulk inserting {} OTUs, this can take a while...'.format(len(otus)))
    otus = OTU.objects.insert(otus)
    log.info('Done inserting junctions')
    return otus

def phase2(csvindex):
    global log
    log.info('=' * 60)
    log.info('Phase 2. Update created objects with CSV index')
    log.info('=' * 60)
    for junc in csvindex:
        print(junc)

def read_args_params(args):
    global log
    pattern = re.compile(r'J\d{6}\-\d{8}')
    with open(args.input, 'r') as jdf:
        jsdata = json.load(jdf)
    log.info('We have {} keys to upload from JSON'.format(len(jsdata)))
    csvindex = []
    with open(args.index, 'r', encoding='utf-8-sig') as fp:
        reader = csv.reader(fp, delimiter=';')
        for line in reader:
            if line[0] != '' and line[1] != '' and line[2] != '' and pattern.match(line[3]):
                csvindex.append(line)
    log.info('We have {} junctions in the CSV index'.format(len(csvindex)))
    return jsdata, csvindex

if __name__ == "__main__":
    global log
    setup_logging()
    log.info('Started seed-db script')
    args = setup_args()
    jsdata, csvindex = read_args_params(args)
    # connect('dacot-dev', host=args.mongo)
    phase2(csvindex)
    log.info('DONE SEEDING THE DB')
