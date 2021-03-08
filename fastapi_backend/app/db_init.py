import json
from dacot_models import APIKeyUsers
from mongoengine.errors import NotUniqueError

class DBInit:
    def __init__(self, infile):
        self.__read_users(infile)

    def __read_users(self, infile):
        with open(infile, 'r') as fp:
            self.__users = json.load(fp)
    
    def __create_apikey_users(self):
        for user in self.__users['users']:
            model = APIKeyUsers(key=user['key'], secret=user['secret'])
            try:
                model.save()
            except NotUniqueError:
                continue

    def init(self):
        self.__create_apikey_users()
