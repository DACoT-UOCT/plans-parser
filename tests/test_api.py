import os

os.environ['mongo_db'] = 'testing-db'
os.environ['mongo_uri'] = 'mongomock://127.0.0.1'
os.environ['RUNNING_TEST'] = 'OK'

import unittest
from fastapi_backend.app import main as production_main
from fastapi.testclient import TestClient
from deploy.seed_db_module import seed_from_interpreter

class TestFastAPI(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFastAPI, self).__init__(*args, **kwargs)
        self.client = TestClient(production_main.app)

    @classmethod
    def setUpClass(cls):
        seed_from_interpreter(
            os.environ.get('mongo_uri'), os.environ.get('mongo_db'),
            'tests/cmodels.csv', 'tests/juncs.csv', 'tests/scheds.json'
        )

    def test_get_api_root(self): #FIXME: This should return a not authorized error
        response = self.client.get("/")
        # print(response)
        # print(response.json())
        assert response.status_code == 200 # See FIXME

    def test_action_log_get_faltan_parametros(self):
        response = self.client.get('/actions_log')
        assert response.status_code == 422

    def test_action_log_get_parametros_ok_user_no_existe(self):
        response = self.client.get('/actions_log?user_email=user@dominio.cl')
        assert response.status_code == 404
        assert response.json()['detail'] == 'User user@dominio.cl not found'

    def test_get_users(self):
        response = self.client.get('/users?user_email=admin@dacot.uoct.cl')
        assert response.status_code == 200
        emails = set([u['email'] for u in response.json()])
        assert 'admin@dacot.uoct.cl' in emails
        assert 'seed@dacot.uoct.cl' in emails

    def test_get_users_not_admin(self):
        response = self.client.get('/users?user_email=employee@acmecorp.com')
        assert response.status_code == 403
        assert response.json()['detail'] == 'Forbidden'
        # print(response, response.json())

    def test_get_users_user_not_found(self):
        response = self.client.get('/users?user_email=user@dominio.cl')
        assert response.status_code == 404
        assert response.json()['detail'] == 'User user@dominio.cl not found'

    # FIXME: Test /edit-user/ and /delet-user/