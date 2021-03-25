import re
import csv
import json
import datetime
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

class APISeed:
    def __init__(self, api_url, file_ctrl_models, file_junctions, file_schedules, file_communes):
        self.__seed_params = self.__setup_params(api_url, file_ctrl_models, file_junctions, file_schedules, file_communes)
        self.__api = None

    def __setup_api_client(self):
        transport = AIOHTTPTransport(url=self.__seed_params['backend_url'])
        self.__api = Client(transport=transport, fetch_schema_from_transport=True)
        self.__login_api()

    def __login_api(self):
        res = self.__api.execute(gql('query {{ loginApiKey(key: "{}", secret: "{}") }}'.format(
            self.__api_key,
            self.__secret_key
        )))
        self.__api_token = res['loginApiKey']

    def __read_ctrl_models(self, infile):
        models = []
        with open(infile, 'r', encoding="utf-8-sig") as fp:
            reader = csv.reader(fp, delimiter=";")
            for line in reader:
                models.append(line)
        return models

    def __read_schedules(self, infile):
        with open(infile, 'r') as fp:
            data = json.load(fp)
            return data

    def __read_junctions_index(self, infile):
        index = {}
        junc_re = re.compile(r'J\d{6}\-\d{8}')
        otu_re = re.compile(r'X\d{6}')
        with open(infile, 'r', encoding="utf-8-sig") as fp:
            reader = csv.reader(fp, delimiter=";")
            for line in reader:
                if line[0] and line[1] and line[2] and junc_re.match(line[3]) and otu_re.match(line[2]):
                    oid, jid = line[2], line[1]
                    key = '{}.{}'.format(oid, jid)
                    index[key] = {
                        'line': line,
                        'jid': jid,
                        'oid': oid
                    }
        return index

    def __read_initial_users(self):
        role = 'Personal UOCT'
        return [{
            'name': 'SpeeDevs',
            'users': [
                {'full_name': 'DACoT DataBase Seed', 'email': 'seed@dacot.uoct.cl', 'role': role, 'area': 'TIC', 'admin': False},
                {'full_name': 'Admin', 'email': 'admin@dacot.uoct.cl', 'role': role, 'area': 'TIC', 'admin': True},
                {'full_name': 'Carlos Ponce', 'email': 'carlos.ponce@sansano.usm.cl', 'role': role, 'area': 'TIC', 'admin': True},
                {'full_name': 'Sebastian Muñoz', 'email': 'sebastian.munozd@sansano.usm.cl', 'role': role, 'area': 'TIC', 'admin': True}
            ]
        }]

    def __read_communes(self, infile):
        # INFO: Data was read from https://apis.digital.gob.cl/dpa/regiones/13/comunas
        list_of_communes = []
        with open(infile, 'r') as fp:
            communes = json.load(fp)
            for commune in communes:
                list_of_communes.append({
                    'name': commune.get('nombre').upper(),
                    'code': commune.get('codigo')
                })
        list_of_communes.append({
            'name': 'SIN ASIGNAR',
            'code': 0
        })
        return list_of_communes

    def __setup_params(self, backend, ctrl, juncs, sched, communes):
        return {
            'ctrl_models': self.__read_ctrl_models(ctrl),
            'junctions': self.__read_junctions_index(juncs),
            'users': self.__read_initial_users(),
            'communes': self.__read_communes(communes),
            'schedules': self.__read_schedules(sched),
            'backend_url': backend
        }

    def __drop_old_data(self):
        res = self.__api.execute(gql('query { fullSchemaDrop }'))
        return res['fullSchemaDrop']

    def __create_company(self, company_name):
        query = '''
            mutation {{
                createCompany(companyDetails: {{
                    name: "{}"
                }}) {{ id }}
            }}
        '''.format(company_name)
        self.__api.execute(gql(query))

    def __create_users(self):
        for company in self.__seed_params['users']:
            company_name = company['name']
            self.__create_company(company_name)
            for user in company['users']:
                query = '''
                mutation {{
                    createUser(userDetails: {{
                        isAdmin: {},
                        fullName: "{}",
                        email: "{}",
                        role: "{}",
                        area: "{}",
                        company: "{}"
                    }}) {{ id }}
                }}'''.format(str(user['admin']).lower(), user['full_name'], user['email'], user['role'], user['area'], company_name)
                self.__api.execute(gql(query))

    def __create_comunes(self):
        for commune in self.__seed_params['communes']:
            query = '''
                mutation {{
                    createCommune(communeDetails: {{
                        code: {},
                        name: "{}"
                    }}) {{ code }}
                }}
            '''.format(commune['code'], commune['name'])
            self.__api.execute(gql(query))

    def __get_existing_companies(self):
        query = 'query { companies { name } }'
        res = self.__api.execute(gql(query))
        ret = set()
        for company in res['companies']:
            ret.add(company['name'])
        return ret

    def __create_controller_models(self):
        existing_companies = self.__get_existing_companies()
        for model in self.__seed_params['ctrl_models']:
            company = model[0].strip().upper()
            model_name = model[1].strip().upper()
            fw_ver = model[2]
            checksum = model[3]
            query = '''
                mutation {{
                    createController(controllerDetails: {{
                        company: "{}",
                        model: "{}",
                        firmwareVersion: "{}",
                        checksum: "{}"
                    }}) {{ id }}
                }}
            '''.format(company, model_name, fw_ver, checksum)
            if company not in existing_companies:
                self.__create_company(company)
                existing_companies.add(company)
            self.__api.execute(gql(query))

    def __create_single_controller_model(self, model):
        company = model[0].strip().upper()
        model_name = model[1].strip().upper()
        fw_ver = model[2]
        checksum = model[3]
        query = '''
            mutation {{
                createController(controllerDetails: {{
                    company: "{}",
                    model: "{}",
                    firmwareVersion: "{}",
                    checksum: "{}"
                }}) {{ id }}
            }}
        '''.format(company, model_name, fw_ver, checksum)
        self.__api.execute(gql(query))

    def __get_existing_communes(self):
        query = 'query { communes { name code } }'
        res = self.__api.execute(gql(query))
        ret = {}
        for commune in res['communes']:
            ret[commune['name']] = commune['code']
        return ret

    def __create_temp_otus(self):
        res = {}
        for junc in self.__seed_params['junctions'].values():
            line = junc['line']
            print(line)
            print(line[8])
            if not junc['oid'] in res:
                common = {}
                common['oid'] = junc['oid']
                common['commune'] = line[6].strip().upper()
                common['maintainer'] = line[7].strip().upper()
                common['model'] = line[8],
                common['model_company'] = line[9].strip().upper()
                print(common)
                res[junc['oid']] = {
                    'common': common,
                    'juncs': []
                }
            current_junc = {
                'sale_id': line[0],
                'jid': junc['jid'],
                'address': '{} - {} - {}'.format(line[4].strip().upper(), line[5].strip().upper(), line[6].strip().upper())
            }
            lat = 0.0
            lon = 0.0
            if line[10] and line[11]:
                try:
                    lat = float(line[10].replace(',', '.'))
                    lon = float(line[11].replace(',', '.'))
                    if not (-90 < lat < 90 and -180 < lon < 180):
                        raise ValueError()
                except ValueError:
                    lat = 0.0
                    lon = 0.0
            current_junc['lat'] = lat
            current_junc['lon'] = lon
            res[junc['oid']]['juncs'].append(current_junc)
        return res.values()

    def __build_junctions_section(self, juncs):
        temp_juncs = []
        for junc in juncs:
            jstr = '{{ jid: "{}", metadata: {{ coordinates: [{}, {}], addressReference: "{}" }} }}'.format(
                junc['jid'], junc['lat'], junc['lon'], junc['address']
            )
            temp_juncs.append(jstr)
        return '[' + ', '.join(str(i) for i in temp_juncs) + ']'

    def __build_projects(self):
        existing_communes = self.__get_existing_communes()
        existing_companies = self.__get_existing_companies()
        created_partial_models = set()
        for otu in self.__create_temp_otus():
            commune_code = existing_communes.get(otu['common']['commune'], 0)
            company = otu['common']['maintainer']
            model = (otu['common']['model_company'], otu['common']['model'], 'Desconocido', 'Desconocido')
            if model not in created_partial_models:
                self.__create_single_controller_model(model)
                created_partial_models.add(model)
            if company not in existing_companies:
                self.__create_company(company)
                existing_companies.add(company)
            query_junctions_section = self.__build_junctions_section(otu['juncs'])
            print(query_junctions_section)
            query = '''
                mutation {{
                    createProject(projectDetails: {{
                        oid: "{}",
                        metadata: {{
                            commune: {},
                            maintainer: "{}"
                        }},
                        otu: {{
                            junctions: {}
                        }},
                        controller: {{
                            model: {{
                                company: "{}",
                                model: "{}",
                                firmwareVersion: "{}",
                                checksum: "{}"
                            }}
                        }}
                        observation: "Created in Seed Script"
                    }}) {{ oid jid }}
                }}
            '''.format(
                otu['common']['oid'], commune_code, company, query_junctions_section,
                model[0], model[1], model[2], model[3]
            )
            self.__api.execute(gql(query))

    def __build_schedules(self):
        for sched in self.__seed_params['schedules'].items():
            pass

    def runtime_seed(self):
        if not self.__api:
            raise RuntimeError('You have to call set_api_credentials first')
        if not self.__drop_old_data():
            raise RuntimeError('Failed to drop old data from db')
        self.__create_users()
        self.__create_comunes()
        self.__create_controller_models()
        self.__build_projects()
        # Accept new projects
        self.__build_schedules()
        # Accept updates

    def set_api_credentials(self, key, secret_key):
        self.__api_key = key
        self.__secret_key = secret_key
        self.__setup_api_client()
