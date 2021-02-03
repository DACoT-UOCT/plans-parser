import logging
import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineObjectType
from models import User as UserModel
from models import ExternalCompany as ExternalCompanyModel
from models import ActionsLog as ActionsLogModel
from models import Commune as CommuneModel
from mongoengine import ValidationError, NotUniqueError
from graphql import GraphQLError

class CustomMutation(graphene.Mutation):
    # TODO: FIXME: Send emails functions
    # TODO: FIXME: Add current user to log
    class Meta:
        abstract = True

    @classmethod
    def log_action(cls, message, graphql_info):
        op = str(graphql_info.operation)
        log = ActionsLogModel(user='None', context=op, action=message, origin='GraphQL API')
        log.save()

class ExternalCompany(MongoengineObjectType):
    class Meta:
        model = ExternalCompanyModel
        interfaces = (Node,)

class User(MongoengineObjectType):
    class Meta:
        model = UserModel
        interfaces = (Node,)

class ActionsLog(MongoengineObjectType):
    class Meta:
        model = ActionsLogModel
        interfaces = (Node,)

class Commune(MongoengineObjectType):
    class Meta:
        model = CommuneModel
        interfaces = (Node,)

class Query(graphene.ObjectType):
    users = graphene.List(User)
    user = graphene.Field(User, email=graphene.NonNull(graphene.String))
    actions_logs = graphene.List(ActionsLog)
    actions_log = graphene.Field(ActionsLog, logid=graphene.NonNull(graphene.String))
    communes = graphene.List(Commune)

    def resolve_communes(self, info):
        return list(CommuneModel.objects.all())

    def resolve_actions_logs(self, info):
        return list(ActionsLogModel.objects.all())

    def resolve_actions_log(self, info, logid):
        return ActionsLogModel.objects(id=logid).first()

    def resolve_users(self, info):
        return list(UserModel.objects.all())

    def resolve_user(self, info, email):
        return UserModel.objects(email=email).first()

class UpdateCommuneInput(graphene.InputObjectType):
    code = graphene.NonNull(graphene.Int)
    maintainer = graphene.String()
    user_in_charge = graphene.String()

class UpdateCommune(CustomMutation):
    class Arguments:
        commune_details = UpdateCommuneInput()

    Output = Commune

    @classmethod
    def mutate(cls, root, info, commune_details):
        commune = CommuneModel.objects(code=commune_details.code).first()
        if not commune:
            cls.log_action('Failed to update commune "{}". Commune not found'.format(commune_details.code), info)
            return GraphQLError('Commune "{}" not found'.format(commune_details.code))
        if commune_details.maintainer != None:
            maintainer = ExternalCompanyModel.objects(name=commune_details.maintainer).first()
            if not maintainer:
                cls.log_action('Failed to update commune "{}". Maintainer "{}" not found'.format(commune_details.code, commune_details.maintainer), info)
                return GraphQLError('Maintainer "{}" not found'.format(commune_details.maintainer))
            commune.maintainer = maintainer
        if commune_details.user_in_charge != None:
            user = UserModel.objects(email=commune_details.user_in_charge).first()
            if not user:
                cls.log_action('Failed to update commune "{}". User "{}" not found'.format(commune_details.code, commune_details.user_in_charge), info)
                return GraphQLError('User "{}" not found'.format(commune_details.user_in_charge))
            commune.user_in_charge = user
        try:
            commune.save()
        except ValidationError as excep:
            cls.log_action('Failed to update commune "{}". {}'.format(commune.name, excep), info)
            return GraphQLError(excep)
        cls.log_action('Commune "{}" updated.'.format(commune.name), info)
        return commune

class CreateUserInput(graphene.InputObjectType):
    is_admin = graphene.NonNull(graphene.Boolean)
    full_name = graphene.NonNull(graphene.String)
    email = graphene.NonNull(graphene.String)
    role = graphene.NonNull(graphene.String)
    area = graphene.NonNull(graphene.String)
    company = graphene.String()

class CreateUser(CustomMutation):
    class Arguments:
        user_details = CreateUserInput()

    Output = User

    @classmethod
    def mutate(cls, root, info, user_details):
        user = UserModel()
        user.is_admin = user_details.is_admin
        user.full_name = user_details.full_name
        user.email = user_details.email
        user.role = user_details.role
        user.area = user_details.area
        if user_details.company:
            user.company = ExternalCompanyModel.objects(name=user_details.company).first()
            if not user.company:
                cls.log_action('Failed to create user "{}". ExternalCompany "{}" not found'.format(user.email, user_details.company), info)
                return GraphQLError('ExternalCompany "{}" not found'.format(user_details.company))
        try:
            user.save()
        except (ValidationError, NotUniqueError) as excep:
            cls.log_action('Failed to create user "{}". {}'.format(user.email, excep), info)
            return GraphQLError(excep)
        cls.log_action('User "{}" created'.format(user.email), info)
        return user

class DeleteUserInput(graphene.InputObjectType):
    email = graphene.NonNull(graphene.String)

class DeleteUser(CustomMutation):
    class Arguments:
        user_details = DeleteUserInput()

    Output = graphene.String

    @classmethod
    def mutate(cls, root, info, user_details):
        user = UserModel.objects(email=user_details.email).first()
        if not user:
            cls.log_action('Failed to delete user "{}". User not found'.format(user_details.email), info)
            return GraphQLError('User "{}" not found'.format(user_details.email))
        uid = user.id
        user.delete()
        cls.log_action('User "{}" deleted'.format(user_details.email), info)
        return uid

class UpdateUserInput(graphene.InputObjectType):
    email = graphene.NonNull(graphene.String)
    is_admin = graphene.Boolean()
    full_name = graphene.String()

class UpdateUser(CustomMutation):
    class Arguments:
        user_details = UpdateUserInput()

    Output = User

    @classmethod
    def mutate(cls, root, info, user_details):
        user = UserModel.objects(email=user_details.email).first()
        if not user:
            cls.log_action('Failed to update user "{}". User not found'.format(user_details.email), info)
            return GraphQLError('User "{}" not found'.format(user_details.email))
        if user_details.is_admin != None:
            user.is_admin = user_details.is_admin
        if user_details.full_name != None:
            user.full_name = user_details.full_name
        try:
            user.save()
        except ValidationError as excep:
            cls.log_action('Failed to update user "{}". {}'.format(user_details.email, excep), info)
            return GraphQLError(excep)
        cls.log_action('User "{}" updated.'.format(user_details.email), info)
        return user

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    delete_user = DeleteUser.Field()
    update_user = UpdateUser.Field()
    update_commune = UpdateCommune.Field()

dacot_schema = graphene.Schema(query=Query, mutation=Mutation)

class GraphQLLogFilter(logging.Filter):
    def filter(self, record):
        if 'graphql.error.located_error.GraphQLLocatedError:' in record.msg:
            return False
        return True

# Disable graphene logging
logging.getLogger('graphql.execution.utils').addFilter(GraphQLLogFilter())
