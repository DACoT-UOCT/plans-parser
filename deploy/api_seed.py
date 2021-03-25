import re
import csv
import json
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
                    'name': commune.get('nombre'),
                    'code': commune.get('codigo')
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

    def __create_users(self):
        print()
        for company in self.__seed_params['users']:
            company_name = company['name']
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
                res = self.__api.execute(gql(query))
                print(res)

    def runtime_seed(self):
        if not self.__api:
            raise RuntimeError('You have to call set_api_credentials first')
        if not self.__drop_old_data():
            raise RuntimeError('Failed to drop old data from db')
        self.__create_users()

    def set_api_credentials(self, key, secret_key):
        self.__api_key = key
        self.__secret_key = secret_key
        self.__setup_api_client()
