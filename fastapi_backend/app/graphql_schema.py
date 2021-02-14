import magic
import base64
import logging
import graphene
from graphene_mongo import MongoengineObjectType
from models import User as UserModel
from models import ExternalCompany as ExternalCompanyModel
from models import ActionsLog as ActionsLogModel
from models import Commune as CommuneModel
from models import Project as ProjectModel
from models import Comment as CommentModel
from models import ControllerModel as ControllerModelModel
from models import OTU as OTUModel
from models import OTUMeta as OTUMetaModel
from models import OTUProgramItem as OTUProgramItemModel
from models import OTUSequenceItem as OTUSequenceItemModel
from models import OTUPhasesItem as OTUPhasesItemModel
from models import OTUStagesItem as OTUStagesItemModel
from models import Project as ProjectModel
from models import ProjectMeta as ProjectMetaModel
from models import Junction as JunctionModel
from models import JunctionMeta as JunctionMetaModel
from models import JunctionPlan as JunctionPlanModel
from models import JunctionPlanPhaseValue as JunctionPlanPhaseValueModel
from models import JunctionPlanIntergreenValue as JunctionPlanIntergreenValueModel
from models import PlanParseFailedMessage as PlanParseFailedMessageModel
from mongoengine import ValidationError, NotUniqueError
from graphql import GraphQLError

class Project(MongoengineObjectType):
    class Meta:
        model = ProjectModel

class JunctionMeta(MongoengineObjectType):
    class Meta:
        model = JunctionMetaModel

class JunctionPlan(MongoengineObjectType):
    class Meta:
        model = JunctionPlanModel

class JunctionPlanPhaseValue(MongoengineObjectType):
    class Meta:
        model = JunctionPlanPhaseValueModel

class JunctionPlanIntergreenValue(MongoengineObjectType):
    class Meta:
        model = JunctionPlanIntergreenValueModel

class Junction(MongoengineObjectType):
    class Meta:
        model = JunctionModel

class OTUStagesItem(MongoengineObjectType):
    class Meta:
        model = OTUStagesItemModel

class OTUPhasesItem(MongoengineObjectType):
    class Meta:
        model = OTUPhasesItemModel

class OTUSequenceItem(MongoengineObjectType):
    class Meta:
        model = OTUSequenceItemModel

class Comment(MongoengineObjectType):
    class Meta:
        model = CommentModel

class PlanParseFailedMessage(MongoengineObjectType):
    class Meta:
        model = PlanParseFailedMessageModel

class PartialPlanParseFailedMessage(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    date = graphene.NonNull(graphene.DateTime)
    comment = graphene.NonNull(Comment)

class ExternalCompany(MongoengineObjectType):
    class Meta:
        model = ExternalCompanyModel

class User(MongoengineObjectType):
    class Meta:
        model = UserModel

class ActionsLog(MongoengineObjectType):
    class Meta:
        model = ActionsLogModel

class Commune(MongoengineObjectType):
    class Meta:
        model = CommuneModel

class ControllerModel(MongoengineObjectType):
    class Meta:
        model = ControllerModelModel

class OTU(MongoengineObjectType):
    class Meta:
        model = OTUModel

class OTUMeta(MongoengineObjectType):
    class Meta:
        model = OTUMetaModel

class OTUProgramItem(MongoengineObjectType):
    class Meta:
        model = OTUProgramItemModel

class CustomMutation(graphene.Mutation):
    # TODO: FIXME: Send emails functions
    # TODO: FIXME: Add current user to log
    # TODO: FIXME: Make log in background_task
    # TODO: FIXME: Replace all '{something}id' to 'id'
    # TODO: FIXME: Move models folder to a local pip package
    class Meta:
        abstract = True

    @classmethod
    def log_action(cls, message, graphql_info):
        op = str(graphql_info.operation)
        current_user = cls.get_current_user()
        log = ActionsLogModel(user=current_user.email, context=op, action=message, origin='GraphQL API')
        log.save()

    @classmethod
    def get_current_user(cls):
        # Returns the currently logged user
        # TODO: FIXME: For now, we return the same user for all requests
        return UserModel.objects(email='seed@dacot.uoct.cl').first()

    def get_b64file_data(cls, base64data):
        _, filedata = base64data.split(',')
        b64bytes = base64.b64decode(filedata)
        mime = magic.from_buffer(b64bytes[0:2048], mime=True)
        return b64bytes, mime

class Query(graphene.ObjectType):
    users = graphene.List(User)
    user = graphene.Field(User, email=graphene.NonNull(graphene.String))
    actions_logs = graphene.List(ActionsLog)
    actions_log = graphene.Field(ActionsLog, logid=graphene.NonNull(graphene.String))
    communes = graphene.List(Commune)
    companies = graphene.List(ExternalCompany)
    failed_plans = graphene.List(PartialPlanParseFailedMessage)
    failed_plan = graphene.Field(PlanParseFailedMessage, mid=graphene.NonNull(graphene.String))
    controller_models = graphene.List(ControllerModel)
    otus = graphene.List(OTU)
    otu = graphene.Field(OTU, oid=graphene.NonNull(graphene.String))
    junctions = graphene.List(Junction)
    junction = graphene.Field(Junction, jid=graphene.NonNull(graphene.String))

    def resolve_junctions(self, info):
        juncs = []
        projects = ProjectModel.objects.only('otu.junctions').all()
        for proj in projects:
            juncs.extend(proj.otu.junctions)
        return juncs

    def resolve_junction(self, info, jid):
        proj = ProjectModel.objects(otu__junctions__jid=jid).only('otu.junctions').first()
        if proj:
            for junc in proj.junctions:
                if junc.jid == jid:
                    return junc
        return None

    def resolve_otus(self, info):
        projects = ProjectModel.objects.only('otu').all()
        return [proj.otu for proj in projects]

    def resolve_otu(self, info, oid):
        proj = ProjectModel.objects(oid=oid).only('otu').first()
        if proj:
            return proj.otu
        return None

    def resolve_controller_models(self, info):
        return list(ControllerModelModel.objects.all())

    def resolve_failed_plans(self, info):
        return list(PlanParseFailedMessageModel.objects.only('id', 'date', 'comment').all())

    def resolve_failed_plan(self, info, mid):
        return PlanParseFailedMessageModel.objects(id=mid).first()

    def resolve_companies(self, info):
        return list(ExternalCompanyModel.objects.all())

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

class ControllerModelInput(graphene.InputObjectType):
    company = graphene.NonNull(graphene.String)
    model = graphene.NonNull(graphene.String)
    firmware_version = graphene.NonNull(graphene.String)
    checksum = graphene.NonNull(graphene.String)

class ControllerLocationInput(graphene.InputObjectType):
    address_reference = graphene.String()
    gps = graphene.Boolean()
    model = graphene.NonNull(ControllerModelInput)

class ProjectHeadersInput(graphene.InputObjectType):
    hal = graphene.NonNull(graphene.Int)
    led = graphene.NonNull(graphene.Int)
    type = graphene.NonNull(graphene.String)

class ProjectUPSInput(graphene.InputObjectType):
    brand = graphene.NonNull(graphene.String)
    model = graphene.NonNull(graphene.String)
    serial = graphene.NonNull(graphene.String)
    capacity = graphene.NonNull(graphene.String)
    charge_duration = graphene.NonNull(graphene.String)

class ProjectPolesInput(graphene.InputObjectType):
    hooks = graphene.NonNull(graphene.Int)
    vehicular = graphene.NonNull(graphene.Int)
    pedestrian = graphene.NonNull(graphene.Int)

class ProjectMetaInput(graphene.InputObjectType):
    installation_date = graphene.Date()
    installation_company = graphene.String()
    maintainer = graphene.NonNull(graphene.String)
    commune = graphene.NonNull(graphene.Int)
    img = graphene.Base64()
    pdf_data = graphene.Base64()
    pedestrian_demand = graphene.Boolean()
    pedestrian_facility = graphene.Boolean()
    local_detector = graphene.Boolean()
    scoot_detector = graphene.Boolean()

class OTUMetadataInput(graphene.InputObjectType):
    serial = graphene.String()
    ip_address = graphene.String()
    netmask = graphene.String()
    control = graphene.Int()
    answer = graphene.Int()
    link_type = graphene.String()
    link_owner = graphene.String()

class OTUProgramInput(graphene.InputObjectType):
    day = graphene.NonNull(graphene.String)
    time = graphene.NonNull(graphene.String)
    plan = graphene.NonNull(graphene.String)

class JunctionMetadataInput(graphene.InputObjectType):
    coordinates = graphene.NonNull(graphene.List(graphene.NonNull(graphene.Float)))
    sales_id = graphene.NonNull(graphene.Int)
    address_reference = graphene.NonNull(graphene.String)

class ProjectJunctionInput(graphene.InputObjectType):
    jid = graphene.NonNull(graphene.String)
    metadata = graphene.NonNull(JunctionMetadataInput)

class ProjectOTUInput(graphene.InputObjectType):
    metadata = OTUMetadataInput()
    junctions = graphene.NonNull(graphene.List(graphene.NonNull(ProjectJunctionInput)))

class CreateProjectInput(graphene.InputObjectType):
    oid = graphene.NonNull(graphene.String)
    metadata = graphene.NonNull(ProjectMetaInput)
    otu = graphene.NonNull(ProjectOTUInput)
    controller = graphene.NonNull(ControllerLocationInput)
    headers = graphene.List(ProjectHeadersInput)
    ups = ProjectUPSInput()
    poles = ProjectPolesInput()
    observations = graphene.NonNull(graphene.List(graphene.String))

class CreateProject(CustomMutation):
    class Arguments:
        project_details = CreateProjectInput()

    Output = Project

    @classmethod
    def build_metadata_files(cls, meta, metain, oid, info):
        if metain.img:
            fdata, ftype = cls.get_b64file_data(metain.img)
            if ftype in ['image/jpeg', 'image/png']:
                meta.img.put(fdata, content_type=ftype)
            else:
                cls.log_action('Failed to create project "{}". Invalid image file type: "{}"'.format(oid, ftype), info)
                return False, GraphQLError('Invalid image file type: "{}"'.format(ftype))
        if metain.pdf_data:
            fdata, ftype = cls.get_b64file_data(metain.pdf_data)
            if ftype in ['application/pdf']:
                meta.pdf_data.put(fdata, content_type=ftype)
            else:
                cls.log_action('Failed to create project "{}". Invalid  file type: "{}"'.format(oid, ftype), info)
                return False, GraphQLError('Invalid PDF document file type: "{}"'.format(ftype))
        return True, meta

    @classmethod
    def build_metadata_options(cls, meta, metain):
        if metain.pedestrian_demand:
            meta.pedestrian_demand = metain.pedestrian_demand
        if metain.pedestrian_facility:
            meta.pedestrian_facility = metain.pedestrian_facility
        if metain.local_detector:
            meta.local_detector = metain.local_detector
        if metain.scoot_detector:
            meta.scoot_detector = metain.scoot_detector
        return meta

    @classmethod
    def build_metadata(cls, metain, oid, info):
        meta = ProjectMetaModel()
        meta.status = 'NEW'
        meta.status_user = cls.get_current_user()
        if metain.installation_date:
            meta.installation_date = metain.installation_date
        if metain.installation_company:
            installation_company = ExternalCompanyModel.objects(name=metain.installation_company).first()
            if not installation_company:
                cls.log_action('Failed to create project "{}". Company "{}" not found'.format(oid, metain.installation_company), info)
                return False, GraphQLError('Company "{}" not found'.format(metain.installation_company))
            meta.installation_company = installation_company
        maintainer = ExternalCompanyModel.objects(name=metain.maintainer).first()
        if not maintainer:
            cls.log_action('Failed to create project "{}". Company "{}" not found'.format(oid, metain.maintainer), info)
            return False, GraphQLError('Company "{}" not found'.format(metain.maintainer))
        meta.maintainer = maintainer
        commune = CommuneModel.objects(code=metain.commune).first()
        if not commune:
            cls.log_action('Failed to create project "{}". Commune "{}" not found'.format(oid, metain.commune), info)
            return False, GraphQLError('Commune "{}" not found'.format(metain.commune))
        meta.commune = commune.name # TODO: FIXME: This should be a reference! Update model
        meta = cls.build_metadata_options(meta, metain)
        return cls.build_metadata_files(meta, metain, oid, info)

    @classmethod
    def mutate(cls, root, info, project_details):
        proj = ProjectModel()
        proj.oid = project_details.oid
        # Metadata
        is_success, meta_result = cls.build_metadata(project_details.metadata, project_details.oid, info)
        if is_success:
            proj.metadata = meta_result
        else:
            return meta_result # Result is a GraphQLError
        # OTU
        is_success, otu_result = cls.build_otu()
        if is_success:
            proj.otu = otu_result
        else:
            return otu_result
        proj.save()
        # TODO: Send notification emails
        return proj

class CreateCommuneInput(graphene.InputObjectType):
    code = graphene.NonNull(graphene.Int)
    name = graphene.NonNull(graphene.String)
    maintainer = graphene.String()
    user_in_charge = graphene.String()

class CreateCommune(CustomMutation):
    class Arguments:
        commune_details = CreateCommuneInput()

    Output = Commune

    @classmethod
    def mutate(cls, root, info, commune_details):
        commune = CommuneModel()
        commune.name = commune_details.name
        commune.code = commune_details.code
        if commune_details.maintainer:
            maintainer = ExternalCompanyModel.objects(name=commune_details.maintainer).first()
            if not maintainer:
                cls.log_action('Failed to create commune "{}". Maintainer "{}" not found'.format(commune_details.code, commune_details.maintainer), info)
                return GraphQLError('Maintainer "{}" not found'.format(commune_details.maintainer))
            commune.maintainer = maintainer
        if commune_details.user_in_charge:
            user = UserModel.objects(email=commune_details.user_in_charge).first()
            if not user:
                cls.log_action('Failed to create commune "{}". User "{}" not found'.format(commune_details.code, commune_details.user_in_charge), info)
                return GraphQLError('User "{}" not found'.format(commune_details.user_in_charge))
            commune.user_in_charge = user
        try:
            commune.save()
        except ValidationError as excep:
            cls.log_action('Failed to create commune "{}". {}'.format(commune.name, excep), info)
            return GraphQLError(excep)
        cls.log_action('Commune "{}" created.'.format(commune.name), info)
        return commune

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
        if commune_details.maintainer:
            maintainer = ExternalCompanyModel.objects(name=commune_details.maintainer).first()
            if not maintainer:
                cls.log_action('Failed to update commune "{}". Maintainer "{}" not found'.format(commune_details.code, commune_details.maintainer), info)
                return GraphQLError('Maintainer "{}" not found'.format(commune_details.maintainer))
            commune.maintainer = maintainer
        if commune_details.user_in_charge:
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
        if user_details.is_admin:
            user.is_admin = user_details.is_admin
        if user_details.full_name:
            user.full_name = user_details.full_name
        try:
            user.save()
        except ValidationError as excep:
            cls.log_action('Failed to update user "{}". {}'.format(user_details.email, excep), info)
            return GraphQLError(excep)
        cls.log_action('User "{}" updated.'.format(user_details.email), info)
        return user

class CreateCompanyInput(graphene.InputObjectType):
    name = graphene.NonNull(graphene.String)

class CreateCompany(CustomMutation):
    class Arguments:
        company_details = CreateCompanyInput()

    Output = ExternalCompany

    @classmethod
    def mutate(cls, root, info, company_details):
        company = ExternalCompanyModel()
        company.name = company_details.name
        try:
            company.save()
        except (ValidationError, NotUniqueError) as excep:
            cls.log_action('Failed to create company "{}". {}'.format(company_details.name, excep), info)
            return GraphQLError(excep)
        cls.log_action('Company "{}" created'.format(company.name), info)
        return company

class DeleteCompanyInput(graphene.InputObjectType):
    name = graphene.NonNull(graphene.String)

class DeleteCompany(CustomMutation):
    class Arguments:
        company_details = DeleteCompanyInput()

    Output = graphene.String

    @classmethod
    def mutate(cls, root, info, company_details):
        company = ExternalCompanyModel.objects(name=company_details.name).first()
        if not company:
            cls.log_action('Failed to delete company "{}". Company not found'.format(company_details.name), info)
            return GraphQLError('Company "{}" not found'.format(company_details.name))
        cid = company.id
        company.delete()
        cls.log_action('Company "{}" deleted'.format(company_details.name), info)
        return cid

class DeletePlanParseFailedMessageInput(graphene.InputObjectType):
    mid = graphene.NonNull(graphene.String)

class DeletePlanParseFailedMessage(CustomMutation):
    class Arguments:
        message_details = DeletePlanParseFailedMessageInput()

    Output = graphene.String

    @classmethod
    def mutate(cls, root, info, message_details):
        message = PlanParseFailedMessageModel.objects(id=message_details.mid).first()
        if not message:
            cls.log_action('Failed to delete parse failed message "{}". Message not found'.format(message_details.mid), info)
            return GraphQLError('Message "{}" not found'.format(message_details.mid))
        mid = message.id
        message.delete()
        cls.log_action('Message "{}" deleted'.format(message_details.mid), info)
        return mid

class CreatePlanParseFailedMessageInput(graphene.InputObjectType):
    plans = graphene.NonNull(graphene.List(graphene.NonNull(graphene.String)))
    message = graphene.NonNull(graphene.String)

class CreatePlanParseFailedMessage(CustomMutation):
    class Arguments:
        message_details = CreatePlanParseFailedMessageInput()

    Output = PlanParseFailedMessage

    @classmethod
    def mutate(cls, root, info, message_details):
        comment = CommentModel()
        comment.message = message_details.message
        comment.author = cls.get_current_user()
        failed_plan = PlanParseFailedMessageModel()
        failed_plan.comment = comment
        failed_plan.plans = message_details.plans
        try:
            failed_plan.save()
        except (ValidationError, NotUniqueError) as excep:
            cls.log_action('Failed to create error message "{}". {}'.format(failed_plan.id, excep), info)
            return GraphQLError(excep)
        cls.log_action('Error message "{}" created'.format(failed_plan.id), info)
        return failed_plan

class CreateControllerModelInput(graphene.InputObjectType):
    company = graphene.NonNull(graphene.String)
    model = graphene.NonNull(graphene.String)
    firmware_version = graphene.String()
    checksum = graphene.String()

class CreateControllerModel(CustomMutation):
    class Arguments:
        controller_details = CreateControllerModelInput()

    Output = ControllerModel

    @classmethod
    def mutate(cls, root, info, controller_details):
        company = ExternalCompanyModel.objects(name=controller_details.company).first()
        if not company:
            cls.log_action('Failed to create model "{}". Company not found'.format(controller_details.model), info)
            return GraphQLError('Company "{}" not found'.format(controller_details.company))
        model = ControllerModelModel()
        model.company = company
        model.model = controller_details.model
        model.firmware_version = controller_details.firmware_version
        model.checksum = controller_details.checksum
        try:
            model.save()
        except (ValidationError, NotUniqueError) as excep:
            cls.log_action('Failed to create model "{}". {}'.format(controller_details.model, excep), info)
            return GraphQLError(excep)
        cls.log_action('Model "{}" created'.format(controller_details.model), info)
        return model

class UpdateControllerModelInput(graphene.InputObjectType):
    cid = graphene.NonNull(graphene.String)
    firmware_version = graphene.String()
    checksum = graphene.String()

class UpdateControllerModel(CustomMutation):
    class Arguments:
        controller_details = UpdateControllerModelInput()

    Output = ControllerModel

    @classmethod
    def mutate(cls, root, info, controller_details):
        model = ControllerModelModel.objects(id=controller_details.cid).first()
        if not model:
            cls.log_action('Failed to update model "{}". Model not found'.format(controller_details.cid), info)
            return GraphQLError('Model "{}" not found'.format(controller_details.cid))
        if controller_details.checksum:
            model.checksum = controller_details.checksum
        if controller_details.firmware_version:
            model.firmware_version = controller_details.firmware_version
        try:
            model.save()
        except ValidationError as excep:
            cls.log_action('Failed to update model "{}". {}'.format(controller_details.cid, excep), info)
            return GraphQLError(excep)
        cls.log_action('Model "{}" updated.'.format(controller_details.cid), info)
        return model

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    delete_user = DeleteUser.Field()
    update_user = UpdateUser.Field()
    update_commune = UpdateCommune.Field()
    create_commune = CreateCommune.Field()
    create_company = CreateCompany.Field()
    delete_company = DeleteCompany.Field()
    delete_failed_plan = DeletePlanParseFailedMessage.Field()
    create_failed_plan = CreatePlanParseFailedMessage.Field()
    create_controller = CreateControllerModel.Field()
    update_controller = UpdateControllerModel.Field()
    create_project = CreateProject.Field()

dacot_schema = graphene.Schema(query=Query, mutation=Mutation)

class GraphQLLogFilter(logging.Filter):
    def filter(self, record):
        if 'graphql.error.located_error.GraphQLLocatedError:' in record.msg:
            return False
        return True

# Disable graphene logging
logging.getLogger('graphql.execution.utils').addFilter(GraphQLLogFilter())
