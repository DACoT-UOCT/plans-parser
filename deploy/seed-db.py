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
from pymongo.errors import BulkWriteError

if os.environ.get('RUNNING_TEST'):
    from .dacot_models import Commune, ExternalCompany, ControllerModel
    from .dacot_models import User, ProjectMeta, OTU, Project, OTUMeta
    from .dacot_models import Controller, Junction, JunctionMeta, JunctionPlan
    from .dacot_models import JunctionPlanPhaseValue, OTUProgramItem
    class log:
        @staticmethod
        def info(msg):
            print(msg)
    is_diff = False
else:
    from dacot_models import Commune, ExternalCompany, ControllerModel
    from dacot_models import User, ProjectMeta, OTU, Project, OTUMeta
    from dacot_models import Controller, Junction, JunctionMeta, JunctionPlan
    from dacot_models import JunctionPlanPhaseValue, OTUProgramItem
    log = None
    is_diff = None # FIXME: Should be a parameter, not a global variable

def setup_logging():
    global log
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    log = logging.getLogger('seed-db')
    log.setLevel(logging.INFO)

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


def setup_args():
    parser = argparse.ArgumentParser(description='Seed the mongo db')
    parser.add_argument('input', type=str, help='input schedules.json file')
    parser.add_argument('index', type=str, help='CSV index file with relevant columns')
    parser.add_argument('ctrlls_data', type=str, help='CSV data of controller models')
    parser.add_argument('mongo', type=str, help='mongo server url')
    parser.add_argument('database', type=str, help='mongo database to use')
    parser.add_argument('--rebuild', action='store_true', help='drop existing data and rebuild collections')
    parser.add_argument('--extra', action='store_true', help='build and save extra data to the remote db')
    parser.add_argument('--diffdb', action='store_true', help='the remote db will be used for patch generation')
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
    ControllerModel.drop_collection()
    User.drop_collection()
    OTU.drop_collection()
    Project.drop_collection()
    Junction.drop_collection()
    log.info('Done dropping data')

def check_csv_line_valid(line, junc_pattern, otu_pattern):
    if line[0] and line[1] and line[2] and junc_pattern.match(line[3]) and otu_pattern.match(line[2]):
        return True, line[2], line[1]
    return False, None, None

def build_csv_index_item(line, ip_pattern):
    d = {}
    if line[6] and line[7]:
        d['commune'] = line[6].strip().upper()
        d['maintainer'] = line[7].strip().upper()
    if line[4] and line[5]:
        d['address_reference'] = '{} - {}'.format(line[4].strip().upper(), line[6].strip().upper())
    if line[8] and line[9]:
        d['otu_model'] = line[8].strip().upper()
        d['otu_company'] = line[9].strip().upper()
    if line[10] and line[11]:
        try:
            lat = float(line[10].replace(',', '.'))
            lon = float(line[11].replace(',', '.'))
            if not (-90 < lat < 90 and -180 < lon < 180):
                raise ValueError()
        except ValueError:
            lat = 0.0
            lon = 0.0
        d['latitude'] = lat
        d['longitude'] = lon
    if ip_pattern.match(line[14]):
        d['ip_address'] = line[14]
    if line[0]:
        d['sales_id'] = int(line[0])
    return d

def read_csv_data(args):
    index = {}
    junc_pattern = re.compile(r'J\d{6}\-\d{8}')
    otu_pattern = re.compile(r'X\d{6}')
    ipaddr_pattern = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    with open(args.index, 'r', encoding='utf-8-sig') as fp:
        reader = csv.reader(fp, delimiter=';')
        for line in reader:
            valid, oid, jid = check_csv_line_valid(line, junc_pattern, otu_pattern)
            if valid:
                key = '{}.{}'.format(oid, jid)
                index[key] = build_csv_index_item(line, ipaddr_pattern)
                index[key]['oid'] = oid
                index[key]['jid'] = jid
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
        'company': line[0].strip().upper(),
        'model': line[1].strip().upper(),
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
    l = []
    s = set()
    for m in models_csv:
        if m['company'] not in s and not ExternalCompany.objects(name=m.get('company')).first():
            l.append(ExternalCompany(name=m.get('company')))
            s.add(m.get('company'))
    fast_validate_and_insert(l, ExternalCompany)
    l = []
    for m in models_csv:
        comp = ExternalCompany.objects(name=m.get('company')).first()
        l.append(
            ControllerModel(company=comp, model=m.get('model'),
                firmware_version=m.get('fw'), checksum=m.get('check'), date=m.get('date'))
        )
    fast_validate_and_insert(l, ControllerModel)

def create_users():
    l = []
    acme_corp = ExternalCompany(name='ACME Corporation').save().reload()
    l.append(User(full_name='DACoT Database Seed', email='seed@dacot.uoct.cl', rol='Personal UOCT', area='TIC'))
    l.append(User(full_name='Admin', email='admin@dacot.uoct.cl', rol='Personal UOCT', area='TIC', is_admin=True))
    l.append(User(full_name='Carlos Ponce', email='carlos.ponce@sansano.usm.cl', rol='Personal UOCT', area='TIC', is_admin=True))
    l.append(User(full_name='Sebastian Muñoz', email='sebastian.munozd@sansano.usm.cl', rol='Personal UOCT', area='TIC', is_admin=True))
    l.append(User(full_name='Nicolas Grandon', email='ngrandon@uoct.cl', rol='Personal UOCT', area='TIC', is_admin=True))
    l.append(User(full_name='ACME Employee', email='employee@acmecorp.com', rol='Empresa', area='Mantenedora', company=acme_corp))
    fast_validate_and_insert(l, User)

def get_companies_dict():
    comp = {}
    for c in ExternalCompany.objects.all():
        comp[c.name] = c
    return comp

def build_project_meta(csv_index):
    r = {}
    comp = get_companies_dict()
    u = User.objects(email='seed@dacot.uoct.cl').first()
    for k, v in csv_index.items():
        rk = k.split('.')[0]
        m = ProjectMeta(version='base', status='SYSTEM', status_user=u)
        m.commune = v.get('commune')
        m.maintainer = comp.get(v.get('maintainer'))
        r[rk] = m
    return r

def build_otu(project_metas):
    global is_diff
    l = []
    d = {}
    for k in project_metas:
        o = OTU(oid=k)
        if is_diff:
            o.version = 'latest'
        l.append(o)
    saved_ids = fast_validate_and_insert(l, OTU)
    for s in saved_ids:
        d[s.oid] = s
    return d

def build_projects(csv_index):
    global is_diff
    metas = build_project_meta(csv_index)
    otus = build_otu(metas)
    comps = get_companies_dict()
    lp = []
    cmodels = {}
    otu_cmodels = {}
    for v in csv_index.values():
        otus.get(v.get('oid')).metadata = OTUMeta()
        otus.get(v.get('oid')).metadata.ip_address = v.get('ip_address')
        cmk = (v.get('otu_company'), v.get('otu_model'))
        if cmk[0] and cmk[1]:
            if not cmk[0] in comps:
                comps[cmk[0]] = ExternalCompany(name=cmk[0]).save().reload()
            if not cmk in cmodels:
                cmodels[cmk] = ControllerModel(company=comps[cmk[0]], model=cmk[1]).save().reload()
            otu_cmodels[v.get('oid')] = cmodels[cmk]
    for s in fast_validate_and_insert(otus.values(), OTU, replace=True):
        otus[s.oid] = s
    for oid in otus:
        p = Project(metadata=metas.get(oid), otu=otus.get(oid), oid=oid)
        if is_diff:
            p.metadata.version = 'latest'
        p.controller = Controller()
        if oid in otu_cmodels:
            p.controller.model = otu_cmodels[oid]
        lp.append(p)
    fast_validate_and_insert(lp, Project)
    return otus

def build_junctions(csv_index, otus):
    global is_diff
    lj = []
    jd = {}
    od = {}
    for k, v in csv_index.items():
        jid = k.split('.')[1]
        j = Junction(jid=jid, metadata=JunctionMeta())
        j.metadata.location = (v.get('latitude', 0.0), v.get('longitude', 0.0))
        j.metadata.address_reference = v.get('address_reference')
        j.metadata.sales_id = v.get('sales_id')
        if is_diff:
            j.version = 'latest'
        lj.append(j)
    saved_jids = fast_validate_and_insert(lj, Junction)
    for saved in saved_jids:
        jd[saved.jid] = saved
    for k, v in csv_index.items():
        oid, jid = k.split('.')
        otus[oid].junctions.append(jd[jid])
    saved_oids = fast_validate_and_insert(otus.values(), OTU, replace=True)
    for saved in saved_oids:
        od[saved.oid] = saved
    return jd, od

def read_json_data(args):
    with open(args.input, 'r') as jsf:
        return json.load(jsf)

def build_junction_plans(junctions, json_data):
    for k, v in json_data.items():
        j = junctions.get(k)
        if j:
            for pid, pval in v['plans'].items():
                s_start = []
                for phid, phvalue in pval['system_start'].items():
                    s_start.append(JunctionPlanPhaseValue(phid=phid, value=phvalue))
                plan = JunctionPlan(plid=pid, cycle=pval['cycle'], system_start=s_start)
                j.plans.append(plan)
    jd = {}
    for j in fast_validate_and_insert(junctions.values(), Junction, replace=True):
        jd[j.jid] = j
    return jd

def build_otu_programs(otus, json_data):
    done = set()
    programs = {}
    for k, v in json_data.items():
        oid = 'X{}0'.format(k[1:-1])
        if not oid in done:
            programs[oid] = v.get('program')
            done.add(oid)
    for k, v in otus.items():
        otu_program = []
        if k in programs:
            for table, items in programs[k].items():
                for item in items:
                    otu_program.append(OTUProgramItem(day=table, time=item[0][:5], plan=item[1]))
        v.program = otu_program
    od = {}
    for o in fast_validate_and_insert(otus.values(), OTU, replace=True):
        od[o.oid] = o
    return od

def build_latest_versions():
    global is_diff
    lstj = []
    lsto = []
    lstp = []
    if is_diff:
        return
    for junc in Junction.objects.all():
        junc.version = 'latest'
        junc.id = None
        lstj.append(junc)
    for otu in OTU.objects.all():
        otu.version = 'latest'
        otu.id = None
        lsto.append(otu)
    for proj in Project.objects.all():
        proj.metadata.version = 'latest'
        proj.id = None
        lstp.append(proj)
    fast_validate_and_insert(lstj, Junction)
    fast_validate_and_insert(lsto, OTU)
    fast_validate_and_insert(lstp, Project)

def rebuild(args):
    if not check_should_continue():
        return
    connect(args.database, host=args.mongo)
    drop_old_data()
    index_csv = read_csv_data(args)
    create_users()
    build_commune_collection(index_csv)
    controllers_model_csv = read_controller_models_csv(args)
    build_controller_model_collection(controllers_model_csv)
    otus = build_projects(index_csv)
    junctions, otus = build_junctions(index_csv, otus)
    json_data = read_json_data(args)
    junctions = build_junction_plans(junctions, json_data)
    otus = build_otu_programs(otus, json_data)
    build_latest_versions()

if __name__ == "__main__":
    setup_logging()
    log.info('Started seed-db script v0.2')
    args = setup_args()
    print(args)
    if args.diffdb:
        is_diff = True
    else:
        is_diff = False
    if args.rebuild:
        rebuild(args)
    log.info('Done Seeding the remote database')

def seed_from_interpreter(uri, db, ctrl, juncs, scheds):
    print('[seed_from_interpreter] Called!')
    args = argparse.Namespace(
        database=db, diffdb=False, extra=False, ctrlls_data=ctrl,
        index=juncs, input=scheds, mongo=uri, rebuild=True
    )
    drop_old_data()
    index_csv = read_csv_data(args)
    create_users()
    build_commune_collection(index_csv)
    controllers_model_csv = read_controller_models_csv(args)
    build_controller_model_collection(controllers_model_csv)
    otus = build_projects(index_csv)
    junctions, otus = build_junctions(index_csv, otus)
    json_data = read_json_data(args)
    junctions = build_junction_plans(junctions, json_data)
    otus = build_otu_programs(otus, json_data)
    build_latest_versions()
