import logging
import graphene
from graphene_mongo import MongoengineObjectType
from models import User as UserModel
from mongoengine import ValidationError
from graphql import GraphQLError

class User(MongoengineObjectType):
    class Meta:
        model = UserModel

class Query(graphene.ObjectType):
    users = graphene.List(User)
    user = graphene.Field(User, email=graphene.NonNull(graphene.String))

    def resolve_users(self, info):
        return list(UserModel.objects.all())

    def resolve_user(self, info, email):
        return UserModel.objects(email=email).first()

class CreateUserInput(graphene.InputObjectType):
    is_admin = graphene.Boolean()
    full_name = graphene.String()
    email = graphene.String()
    role = graphene.String()
    area = graphene.String()

class CreateUser(graphene.Mutation):
    class Arguments:
        user_details = CreateUserInput()

    Output = User

    @staticmethod
    def mutate(parent, info, user_details):
        user = UserModel()
        user.is_admin = user_details.is_admin
        user.full_name = user_details.full_name
        user.email = user_details.email
        user.role = user_details.role
        user.area = user_details.area
        try:
            user.save()
        except ValidationError as excep:
            return GraphQLError(excep)
        return user

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()

dacot_schema = graphene.Schema(query=Query, mutation=Mutation)

class GraphQLLogFilter(logging.Filter):
    def filter(self, record):
        if 'graphql.error.located_error.GraphQLLocatedError:' in record.msg:
            return False
        return True

# Disable graphene logging
logging.getLogger('graphql.execution.utils').addFilter(GraphQLLogFilter())
