import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from models import User as UserModel

class User(MongoengineObjectType):
    class Meta:
        model = UserModel

class Query(graphene.ObjectType):
    users = graphene.List(User)
    def resolve_users(self, info):
        return list(UserModel.objects.all())

dacot_schema = graphene.Schema(query=Query, types=[User])
