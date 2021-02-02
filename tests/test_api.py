import os
import json
import base64
import mongomock
import mongomock.gridfs
from graphene.test import Client as GQLClient

os.environ['mongo_db'] = 'db'
os.environ['mongo_uri'] = 'mongomock://127.0.0.1'
os.environ['RUNNING_TEST'] = 'OK'

import unittest
from fastapi_backend.app import main as production_main
from fastapi_backend.app.graphql_schema import dacot_schema
from fastapi.testclient import TestClient
from deploy.seed_db_module import seed_from_interpreter, drop_old_data

TEST_USER_FULLNAME = 'Test User Full Name'

def reset_db_state():
    seed_from_interpreter(
        os.environ.get('mongo_uri'), os.environ.get('mongo_db'),
        'tests/cmodels.csv', 'tests/juncs.csv', 'tests/scheds.json'
    )

class TestFastAPI(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFastAPI, self).__init__(*args, **kwargs)
        self.client = TestClient(production_main.app)
        self.gql = GQLClient(schema=dacot_schema)
        mongomock.gridfs.enable_gridfs_integration()

    @classmethod
    def setUpClass(cls):
        reset_db_state()

    def setUp(self):
        reset_db_state()

    def test_gql_get_users(self):
        result = self.gql.execute('query { users { email fullName } }')
        emails = [ u['email'] for u in result['data']['users'] ]
        assert 'admin@dacot.uoct.cl' in emails
        assert 'seed@dacot.uoct.cl' in emails

    def test_gql_get_users_single_user(self):
        result = self.gql.execute('query { user(email: "admin@dacot.uoct.cl") { email fullName } }')
        assert result['data']['user']['fullName'] == 'Admin'

    def test_gql_get_users_single_user_and_company(self):
        result = self.gql.execute('query { user(email: "employee@acmecorp.com") { email fullName company { name } } }')
        assert result['data']['user']['email'] == 'employee@acmecorp.com'
        assert result['data']['user']['company']['name'] == 'ACME Corporation'

    def test_gql_get_users_single_user_not_exists(self):
        result = self.gql.execute('query { user(email: "notfound@example.com") { email fullName } }')
        assert result['data']['user'] == None

    def test_gql_get_users_empty_list(self):
        drop_old_data()
        result = self.gql.execute('query { users { email fullName } }')
        assert type(result['data']['users']) == list
        assert len(result['data']['users']) == 0

    def test_gql_get_users_attribute_not_exists(self):
        result = self.gql.execute('query { users { email fullName attribute_not_exists } }')
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'Cannot query field "attribute_not_exists"' in err_messages

    def test_gql_get_users_invalid_query(self):
        result = self.gql.execute('query { {{{ users { email fullName } }')
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'Syntax Error' in err_messages

    def test_gql_create_user(self):
        result = self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: false,
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Empresa",
                area: "Mantenedora"
            })
            {
                id email fullName
            }
        }
        """)
        assert result['data']['createUser']['email'] == 'user@example.org'
        assert result['data']['createUser']['fullName'] == TEST_USER_FULLNAME
        assert result['data']['createUser']['id'] != None
        result = self.gql.execute('query { user(email: "user@example.org") { fullName } }')
        assert result['data']['user']['fullName'] == TEST_USER_FULLNAME

    def test_gql_create_user_is_admin(self):
        result = self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: true,
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Empresa",
                area: "Mantenedora"
            })
            {
                id email fullName isAdmin
            }
        }
        """)
        assert result['data']['createUser']['email'] == 'user@example.org'
        assert result['data']['createUser']['fullName'] == TEST_USER_FULLNAME
        assert result['data']['createUser']['id'] != None
        assert result['data']['createUser']['isAdmin'] == True
        result = self.gql.execute('query { user(email: "user@example.org") { isAdmin fullName } }')
        assert result['data']['user']['fullName'] == TEST_USER_FULLNAME
        assert result['data']['user']['isAdmin'] == True

    def test_gql_create_user_invalid_full_name(self):
        result = self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: true,
                fullName: "A",
                email: "user@example.org",
                role: "Empresa",
                area: "Mantenedora"
            })
            {
                id email fullName
            }
        }
        """)
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'ValidationError' in err_messages
        assert "String value is too short: ['full_name']" in err_messages

    def test_gql_create_user_invalid_email(self):
        result = self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: false,
                fullName: "Test User Full Name",
                email: "user@example@google@cl.org",
                role: "Empresa",
                area: "Mantenedora"
            })
            {
                id email fullName
            }
        }
        """)
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'ValidationError' in err_messages
        assert 'Invalid email address: user@example@google@cl.org' in err_messages

    def test_gql_create_user_invalid_role(self):
        result = self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: false,
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Invalid_ROLE",
                area: "Mantenedora"
            })
            {
                id email fullName
            }
        }
        """)
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'ValidationError' in err_messages
        assert 'Value must be one of' in err_messages
        assert '[\'role\']' in err_messages

    def test_gql_create_user_invalid_area(self):
        result = self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: false,
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Empresa",
                area: "Invalid_AREA"
            })
            {
                id email fullName
            }
        }
        """)
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'ValidationError' in err_messages
        assert 'Value must be one of' in err_messages
        assert '[\'area\']' in err_messages

    def test_gql_create_user_missing_attribute(self):
        result  = self.gql.execute("""
        mutation {
            createUser(userDetails: {
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Empresa",
                area: "Mantenedora"
            })
            {
                id email fullName isAdmin
            }
        }
        """)
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'field "isAdmin": Expected "Boolean!"' in err_messages

    def test_gql_create_user_duplicated(self):
        self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: false,
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Empresa",
                area: "Mantenedora"
            })
            {
                id email fullName
            }
        }
        """)
        result = self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: false,
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Empresa",
                area: "Mantenedora"
            })
            {
                id email fullName
            }
        }
        """)
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'E11000 Duplicate Key Error' in err_messages

    def test_gql_create_user_company(self):
        result = self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: false,
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Empresa",
                area: "Mantenedora",
                company: "ACME Corporation"
            })
            {
                id email fullName company { id name }
            }
        }
        """)
        assert not 'errors' in result
        assert result['data']['createUser']['id'] != None
        assert result['data']['createUser']['company']['name'] == 'ACME Corporation'
        assert result['data']['createUser']['company']['id'] != None

    def test_gql_create_user_company_not_found(self):
        result = self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: false,
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Empresa",
                area: "Mantenedora",
                company: "Fake Company"
            })
            {
                id email fullName
            }
        }
        """)
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'ExternalCompany "Fake Company" not found' in err_messages

    def test_gql_create_user_uoct_role(self):
        result = self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: false,
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Personal UOCT",
                area: "TIC"
            })
            {
                id email fullName isAdmin
            }
        }
        """)
        assert not 'errors' in result
        assert result['data']['createUser']['email'] == 'user@example.org'
        assert result['data']['createUser']['fullName'] == TEST_USER_FULLNAME
        assert result['data']['createUser']['id'] != None
        assert result['data']['createUser']['isAdmin'] == False

    def test_gql_delete_user(self):
        result = self.gql.execute("""
        mutation {
            deleteUser(userDetails: {
                email: "employee@acmecorp.com"
            })
        }
        """)
        assert not 'errors' in result
        assert result['data']['deleteUser'] != None

    def test_gql_delete_user_not_exists(self):
        result = self.gql.execute("""
        mutation {
            deleteUser(userDetails: {
                email: "user_not_found@example.org"
            })
        }
        """)
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'User "user_not_found@example.org" not found' in err_messages

    def test_gql_update_user_admin(self):
        result = self.gql.execute("""
        mutation {
            updateUser(userDetails: {
                email: "employee@acmecorp.com",
                isAdmin: true
            })
            {
                id isAdmin email
            }
        }
        """)
        assert not 'errors' in result
        assert result['data']['updateUser']['email'] == 'employee@acmecorp.com'
        assert result['data']['updateUser']['id'] != None
        assert result['data']['updateUser']['isAdmin'] == True

    def test_gql_update_user_full_name(self):
        result = self.gql.execute("""
        mutation {
            updateUser(userDetails: {
                email: "employee@acmecorp.com",
                fullName: "Updated Full Name Value"
            })
            {
                id fullName email
            }
        }
        """)
        assert not 'errors' in result
        assert result['data']['updateUser']['email'] == 'employee@acmecorp.com'
        assert result['data']['updateUser']['id'] != None
        assert result['data']['updateUser']['fullName'] == 'Updated Full Name Value'

    def test_gql_update_user_not_found(self):
        result = self.gql.execute("""
        mutation {
            updateUser(userDetails: {
                email: "user_not_found@example.org"
            })
            {
                id
            }
        }
        """)
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'User "user_not_found@example.org" not found' in err_messages
    
    def test_gql_update_user_invalid_field(self):
        result = self.gql.execute("""
        mutation {
            updateUser(userDetails: {
                email: "user_not_found@example.org",
                company: "Updated Company Value"
            })
            {
                id
            }
        }
        """)
        assert 'errors' in result
        assert len(result['errors']) > 0
        err_messages = str([ err['message'] for err in result['errors'] ])
        assert 'Argument "userDetails" has invalid value' in err_messages
        assert 'field "company": Unknown field.' in err_messages

    def test_gql_actions_log_get_all_empty(self):
        result = self.gql.execute('query { actionsLogs { action } }')
        assert 'errors' not in result
        assert len(result['data']['actionsLogs']) == 0

    def test_gql_actions_log_get_all_create_user(self):
        self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: false,
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Empresa",
                area: "Mantenedora"
            })
            {
                id email fullName
            }
        }
        """)
        result = self.gql.execute('query { actionsLogs { action } }')
        assert 'errors' not in result
        assert len(result['data']['actionsLogs']) > 0
        assert 'User "user@example.org" created' in result['data']['actionsLogs'][0]['action']

    def test_gql_actions_log_get_all_create_user_failed(self):
        self.gql.execute("""
        mutation {
            createUser(userDetails: {
                isAdmin: false,
                fullName: "Test User Full Name",
                email: "user@example.org",
                role: "Empresa",
                area: "INVALID"
            })
            {
                id email fullName
            }
        }
        """)
        result = self.gql.execute('query { actionsLogs { action } }')
        assert 'errors' not in result
        assert len(result['data']['actionsLogs']) > 0
        assert 'Failed to create user "user@example.org"' in result['data']['actionsLogs'][0]['action']

    def test_gql_actions_log_get_all_delete_user(self):
        self.gql.execute("""
        mutation {
            deleteUser(userDetails: {
                email: "employee@acmecorp.com"
            })
        }
        """)
        result = self.gql.execute('query { actionsLogs { action } }')
        assert 'errors' not in result
        assert len(result['data']['actionsLogs']) > 0
        assert 'User "employee@acmecorp.com" deleted' in result['data']['actionsLogs'][0]['action']

    def test_gql_actions_log_get_all_delete_user_failed(self):
        self.gql.execute("""
        mutation {
            deleteUser(userDetails: {
                email: "user_not_found@example.org"
            })
        }
        """)
        result = self.gql.execute('query { actionsLogs { action } }')
        assert 'errors' not in result
        assert len(result['data']['actionsLogs']) > 0
        assert 'Failed to delete user "user_not_found@example.org"' in result['data']['actionsLogs'][0]['action']

    def test_gql_actions_log_get_all_update_user(self):
        self.gql.execute("""
        mutation {
            updateUser(userDetails: {
                email: "employee@acmecorp.com",
                isAdmin: true
            })
            {
                id
            }
        }
        """)
        result = self.gql.execute('query { actionsLogs { id action } }')
        assert 'errors' not in result
        assert len(result['data']['actionsLogs']) > 0
        assert 'User "employee@acmecorp.com" updated' in result['data']['actionsLogs'][0]['action']

    def test_gql_actions_log_get_all_update_user_not_found(self):
        self.gql.execute("""
        mutation {
            updateUser(userDetails: {
                email: "user_not_found@example.org",
                isAdmin: false
            })
            {
                id
            }
        }
        """)
        result = self.gql.execute('query { actionsLogs { action } }')
        assert 'errors' not in result
        assert len(result['data']['actionsLogs']) > 0
        assert 'Failed to update user "user_not_found@example.org"' in result['data']['actionsLogs'][0]['action']

    def test_gql_actions_log_get_single(self):
        self.gql.execute("""
        mutation {
            updateUser(userDetails: {
                email: "employee@acmecorp.com",
                isAdmin: true
            })
            {
                id
            }
        }
        """)
        result = self.gql.execute('query { actionsLogs { id action } }')
        assert 'errors' not in result
        assert len(result['data']['actionsLogs']) > 0
        assert result['data']['actionsLogs'][0]['id'] != None
        mock_logid = result['data']['actionsLogs'][0]['id']
        logid = str(base64.b64decode(mock_logid)).replace('\'', '').split(':')[1] # mongomock
        qry = 'query {{ actionsLog(logid: "{}") {{ id user context action date }} }}'.format(logid)
        result = self.gql.execute(qry)
        assert 'User "employee@acmecorp.com" updated.' in result['data']['actionsLog']['action']

#    def test_action_log_get_faltan_parametros(self):
#        response = self.client.get('/actions_log')
#        assert response.status_code == 422
#
#    def test_action_log_get_parametros_ok_user_no_existe(self):
#        response = self.client.get('/actions_log?user_email=user@dominio.cl')
#        assert response.status_code == 404
#        assert response.json()['detail'] == 'User user@dominio.cl not found'
#
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