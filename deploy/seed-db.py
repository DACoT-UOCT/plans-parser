import os
import pymongo
import argparse
import json
import logging

from mongoengine import connect

from dacot_models import OTUProgramItem, JunctionPlan, JunctionPlanPhaseValue, Junction, JunctionMeta, OTU
from dacot_models import ExternalCompany, UOCTUser, OTUController, ChangeSet, OTUMeta

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

connect('dacot-dev', host=args.mongo)

log.info('¡¡¡¡DROPPING OLD DATA!!!!')

Junction.drop_collection()
OTU.drop_collection()
ExternalCompany.drop_collection()
UOCTUser.drop_collection()
OTUController.drop_collection()
ChangeSet.drop_collection()

log.info('Done dropping old collections')

log.info('Building models')

seed_user = UOCTUser(uid=1, full_name='DACoT Automated DB Seeder', email='dacot@santiago.uoct.cl', area='TIC', rut='00000000-0')
seed_user = seed_user.save().reload()

junctions = []
# otus = []

created_otus = {}

i = 0
for k, v in jsondata.items():
    i += 1
    p = (i / total) * 100
    log.info('Building model for {} progress {:.2f}%'.format(k, p))
    plans = []
    oid = 'X' + k[1:-1] + '0'
    if not oid in created_otus:
        programs = []
        for day, items in v['program'].items():
            for item in items:
                programs.append(OTUProgramItem(day=day, time=item[0][:5], plan=item[1]))
        metadata = OTUMeta(version='base', status='SYSTEM', status_user=seed_user)
        created_otus[oid] = OTU(oid=oid, program=programs, metadata=metadata)
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
    created_otus[oid].junctions.append(j)

created_otus = created_otus.values()

log.info('Bulk inserting {} OTUs, this can take a while...'.format(len(created_otus)))
created_otus = OTU.objects.insert(created_otus)
log.info('Done inserting junctions')

log.info('DONE SEEDING THE DB')