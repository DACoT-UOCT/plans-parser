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
        new_junc = Junction(jid=k, plans=plans, metadata=JunctionMeta())
        new_junc.validate()
        junctions.append(new_junc)
    log.info('Bulk inserting {} junctions in the remote mongo database, this can take a while...'.format(len(junctions)))
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
    log.info('Bulk inserting {} OTUs in the remote mongo database, this can take a while...'.format(len(otus)))
    otus = OTU.objects.insert(otus)
    log.info('Done inserting junctions')
    log.info('=' * 60)
    log.info('Phase 1. DONE')
    log.info('=' * 60)
    return otus, junctions

def phase2(otus, junctions, csvindex):
    global log
    log.info('=' * 60)
    log.info('Phase 2. Update created objects with CSV index')
    log.info('=' * 60)
    log.info('Updatig existing junctions with CSV metadata')
    for junc in junctions:
        oid = 'X' + junc['jid'][1:6] + '0'
        if oid not in csvindex:
            log.warning('We have OTU oid={} from JSON file but does not exists in the CSV index'.format(oid))
            continue
        elif junc['jid'] not in csvindex[oid]:
            log.warning('We have JUNCTION jid={} from JSON file but does not exists in the CSV index'.format(junc['jid']))
            continue
        index_data = csvindex[oid][junc['jid']]
        junc.metadata.sales_id = index_data['sales_id']
        if 'latitude' in index_data and 'longitude' in index_data:
            junc.metadata.location = (index_data['latitude'], index_data['longitude'])
        else:
            log.warning('Missing location data for jid={} from the CSV index'.format(junc['jid']))
        junc.metadata.first_access = index_data['first_access']
        junc.metadata.second_access = index_data['second_access']
        junc.validate()
    log.info('Bulk updating {} junctions in the remote mongo database, this can take a while...'.format(len(junctions)))
    junctions = Junction.smart_update(junctions)
    log.info('Done updating junctions')
    log.info('Updatig existing OTUs with CSV metadata')
    for otu in otus:
        pass
    log.info('Bulk updating {} OTUs in the remote mongo database, this can take a while...'.format(len(otus)))
    # otus = OTU.smart_update(otus)
    log.info('Done updating OTUs')
    log.info('=' * 60)
    log.info('Phase 2. DONE')
    log.info('=' * 60)

def read_args_params(args):
    global log
    valid_data_pattern = re.compile(r'J\d{6}\-\d{8}')
    lat_lon_pattern = re.compile(r'^(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)$')
    with open(args.input, 'r') as jdf:
        jsdata = json.load(jdf)
    log.info('We have {} keys to upload from JSON'.format(len(jsdata)))
    csvindex = {}
    controller_models = {}
    external_companies = {}
    with open(args.index, 'r', encoding='utf-8-sig') as fp:
        reader = csv.reader(fp, delimiter=';')
        for line in reader:
            if line[0] != '' and line[1] != '' and line[2] != '' and valid_data_pattern.match(line[3]):
                if line[2] not in csvindex:
                    csvindex[line[2]] = {}
                csvindex[line[2]][line[1]] = {
                    'sales_id': int(line[0]),
                    'first_access': line[4],
                    'second_access': line[5],
                    'commune': line[6],
                    'maintainer': line[7],
                    'otu_type': line[12],
                    'tcc': line[13],
                    'ip_address': line[14],
                    'isp': line[15],
                    'head_type': line[19]
                }
                if line[9] != '' and line[9] != '':
                    if (line[9], line[8]) not in controller_models:
                        if line[9] not in external_companies:
                            new_company = ExternalCompany(name=line[9]).save().reload()
                            external_companies[line[9]] = new_company
                        otu_ctrl = OTUController(company=external_companies[line[9]], model=line[8]).save().reload()
                        controller_models[(line[9], line[8])] = otu_ctrl
                    csvindex[line[2]][line[1]]['controller_model'] = controller_models[(line[9], line[8])]
                if line[10] != '' and line[11] != '' and lat_lon_pattern.match(line[10]) and lat_lon_pattern.match(line[11]):
                    csvindex[line[2]][line[1]]['latitude'] = float(line[10].replace(',', '.'))
                    csvindex[line[2]][line[1]]['longitude'] = float(line[11].replace(',', '.'))
                if line[16] == 'SI':
                    csvindex[line[2]][line[1]]['has_ups'] = True
                elif line[16] == 'NO':
                    csvindex[line[2]][line[1]]['has_ups'] = False
                # TODO: Add IP Address
    log.info('We have {} junctions in the CSV index'.format(len(csvindex)))
    print(controller_models)
    return jsdata, csvindex

if __name__ == "__main__":
    global log
    setup_logging()
    log.info('Started seed-db script')
    args = setup_args()
    connect('dacot-dev', host=args.mongo)
    drop_data()
    jsdata, csvindex = read_args_params(args)
    # otus, junctions = phase1(jsdata)
    # phase2(otus, junctions, csvindex)
    log.info('DONE SEEDING THE DB')
