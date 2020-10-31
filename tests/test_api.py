import os

os.environ['mongo_db'] = 'testing-db'
os.environ['mongo_uri'] = 'mongodb://127.0.0.1'

import unittest
from fastapi_backend.app import main as production_main
from fastapi.testclient import TestClient

class TestFastAPI(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFastAPI, self).__init__(*args, **kwargs)
        self.client = TestClient(production_main.app)

    def test_api_get_404_root(self):
        response = self.client.get("/")
        assert response.status_code == 404

    def test_action_log_get_faltan_parametros(self):
        response = self.client.get('/actions_log')
        assert response.status_code == 422

    def test_action_log_get_parametros_ok_user_no_existe(self):
        response = self.client.get('/actions_log?user_email=user@dominio.cl')
        # print(response)
        # print(response.json())
        assert response.status_code == 404
        assert response.json()['detail'] == 'User user@dominio.cl not found'
