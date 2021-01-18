import os
import json
import mongomock
import mongomock.gridfs
from graphene.test import Client as GQLClient

os.environ['mongo_db'] = 'testing-db'
os.environ['mongo_uri'] = 'mongomock://127.0.0.1'
os.environ['RUNNING_TEST'] = 'OK'

import unittest
from fastapi_backend.app import main as production_main
from fastapi_backend.app.graphql_schema import dacot_schema
from fastapi.testclient import TestClient
from deploy.seed_db_module import seed_from_interpreter

class TestFastAPI(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFastAPI, self).__init__(*args, **kwargs)
        self.client = TestClient(production_main.app)
        self.gql = GQLClient(schema=dacot_schema)
        mongomock.gridfs.enable_gridfs_integration()

    @classmethod
    def setUpClass(cls):
        seed_from_interpreter(
            os.environ.get('mongo_uri'), os.environ.get('mongo_db'),
            'tests/cmodels.csv', 'tests/juncs.csv', 'tests/scheds.json'
        )

    def test_gql_get_users(self):
        result = self.gql.execute('query { users { email fullName } }')
        emails = [ u['email'] for u in result['data']['users']]
        assert 'admin@dacot.uoct.cl' in emails
        assert 'seed@dacot.uoct.cl' in emails

#    def test_get_api_root(self): #FIXME: This should return a not authorized error
#        response = self.client.get("/")
#        print(response)
#        print(response.json())
#        assert response.status_code == 200 # See FIXME
#
#    def test_action_log_get_faltan_parametros(self):
#        response = self.client.get('/actions_log')
#        assert response.status_code == 422
#
#    def test_action_log_get_parametros_ok_user_no_existe(self):
#        response = self.client.get('/actions_log?user_email=user@dominio.cl')
#        assert response.status_code == 404
#        assert response.json()['detail'] == 'User user@dominio.cl not found'
#
#    def test_get_users_missing_param(self):
#        response = self.client.get('/users')
#        assert response.status_code == 422
#
#    def test_get_users(self):
#        response = self.client.get('/users?user_email=admin@dacot.uoct.cl')
#        assert response.status_code == 200
#        emails = set([u['email'] for u in response.json()])
#        assert 'admin@dacot.uoct.cl' in emails
#        assert 'seed@dacot.uoct.cl' in emails
#
#    def test_get_users_not_admin(self):
#        response = self.client.get('/users?user_email=employee@acmecorp.com')
#        assert response.status_code == 403
#        assert response.json()['detail'] == 'Forbidden'
#
#    def test_get_users_user_not_found(self):
#        response = self.client.get('/users?user_email=user@dominio.cl')
#        assert response.status_code == 404
#        assert response.json()['detail'] == 'User user@dominio.cl not found'
#
#    # FIXME: Test /edit-user/ and /delet-user/
#
#    def test_get_actions_log(self):
#        self.client.get('/actions_log?user_email=admin@dacot.uoct.cl')
#        response = self.client.get('/actions_log?user_email=admin@dacot.uoct.cl')
#        assert response.status_code == 200
#        assert len(response.json()) > 0
#
#    def test_get_actions_log_not_admin(self):
#        response = self.client.get('/actions_log?user_email=employee@acmecorp.com')
#        assert response.status_code == 403
#        assert response.json()['detail'] == 'Forbidden'
#
#    def test_get_communes(self):
#        response = self.client.get('/communes')
#        assert response.status_code == 200
#        assert len(response.json()) > 0
#
#    # FIXME: Test /edit-commune
#
#    def test_get_controller_models(self):
#        response = self.client.get('/controller_models')
#        assert response.status_code == 200
#        assert len(response.json()) > 0
#
#    def test_get_companies_missing_params(self):
#        response = self.client.get('/companies')
#        assert response.status_code == 422
#
#    def test_get_companies_not_admin(self):
#        response = self.client.get('/companies?user_email=employee@acmecorp.com')
#        assert response.status_code == 403
#        assert response.json()['detail'] == 'Forbidden'
#
#    def test_get_companies_user_not_found(self):
#        response = self.client.get('/companies?user_email=user@dominio.cl')
#        assert response.status_code == 404
#        assert response.json()['detail'] == 'User user@dominio.cl not found'
#
#    def test_get_companies(self):
#        response = self.client.get('/companies?user_email=admin@dacot.uoct.cl')
#        assert response.status_code == 200
#        assert len(response.json()) > 0
#
#    # FIXME: Test failed_plans
#
#    def test_get_junction(self):
#        response = self.client.get('/junctions/J001111')
#        assert response.status_code == 200
#        assert response.json()['jid'] == 'J001111'
#
#    def test_get_junction_not_found(self):
#        response = self.client.get('/junctions/J999999')
#        assert response.status_code == 404
#
#    def test_get_junction_invalid_regex(self):
#        response = self.client.get('/junctions/invalid')
#        assert response.status_code == 422
#
#    def test_get_otu(self):
#        response = self.client.get('/otu/X001110')
#        assert response.status_code == 200
#        assert response.json()['oid'] == 'X001110'
#
#    def test_get_otu_not_found(self):
#        response = self.client.get('/otu/X876540')
#        assert response.status_code == 404
#
#    def test_get_otu_invalid_regex(self):
#        response = self.client.get('/otu/invalid')
#        assert response.status_code == 422
#
#    def test_get_base_project_version(self):
#        response = self.client.get('/versions/X001110/base?user_email=admin@dacot.uoct.cl')
#        assert response.status_code == 200
#        proj = response.json()
#        assert proj['oid'] == 'X001110'
#        assert proj['metadata']['version'] == 'base'
#
#    def test_create_new_project1_create_admin(self):
#        with open('tests/create_proj.json', 'r') as jsf:
#            data = json.load(jsf)
#        response = self.client.post('/requests?user_email=admin@dacot.uoct.cl', data=json.dumps(data))
#        assert response.status_code == 201
#
#    def test_create_new_project1_create_user(self):
#        with open('tests/create_proj.json', 'r') as jsf:
#            data = json.load(jsf)
#        data['otu']['oid'] = 'X999980'
#        response = self.client.post('/requests?user_email=employee@acmecorp.com', data=json.dumps(data))
#        assert response.status_code == 201
#        data['otu']['oid'] = 'X999970'
#        response = self.client.post('/requests?user_email=employee@acmecorp.com', data=json.dumps(data))
#        assert response.status_code == 201
#
#    def test_create_new_project2_get_single_project_admin(self):
#        response = self.client.get('/requests/X999990?user_email=admin@dacot.uoct.cl')
#        assert response.status_code == 200
#        assert len(response.json()) > 0
#
#    def test_create_new_project3_accept_project_admin(self):
#        data = {
#            'comentario': '', 'file': None, 'mails': ['example@example.com']
#        }
#        response = self.client.put('/requests/X999980/accept?user_email=admin@dacot.uoct.cl', data=json.dumps(data))
#        assert response.status_code == 200
#
#    def test_create_new_project3_reject_project_admin(self):
#        data = {
#            'comentario': '', 'file': None, 'mails': ['example@example.com']
#        }
#        response = self.client.put('/requests/X999970/reject?user_email=admin@dacot.uoct.cl', data=json.dumps(data))
#        assert response.status_code == 200
#
#    def test_get_projects_admin(self):
#        response = self.client.get('/requests?user_email=admin@dacot.uoct.cl')
#        assert response.status_code == 200
#        assert len(response.json()) > 0
#
#
#    # FIXME: Test update, get versions and patches
#