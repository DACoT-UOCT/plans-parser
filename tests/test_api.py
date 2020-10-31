import unittest
from fastapi_backend.app.main import app
from fastapi.testclient import TestClient

#app = FastAPI()
#
#
#@app.get("/")
#async def read_main():
#    return {"msg": "Hello World"}


class TestFastAPI(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFastAPI, self).__init__(*args, **kwargs)
        self.client = TestClient(app)

    def test_api_get_root(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert response.json() == {"msg": "Hello World"}
