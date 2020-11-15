import json
from mongoengine import EmbeddedDocument, IntField, EmbeddedDocumentListField
from mongoengine import Document, PointField, StringField, ListField, DateTimeField
from mongoengine import EmbeddedDocumentField, EmailField, FileField, LongField, ReferenceField
from mongoengine import GenericReferenceField, DictField, BooleanField

from mongoengine import get_connection

from mongoengine.errors import ValidationError, NotUniqueError
from pymongo.errors import DuplicateKeyError

from datetime import datetime

# TODO: Make index
# TODO: Deletion flags (Cascade, DENY, etc)

# Junction Model ====

class DACoTBackendException(Exception):
    def __init__(self, status_code=500, details='Internal Server Error'):
        self._code = status_code
        self._detail = details

    def __str__(self):
        return "{}: status_code={} details='{}'".format(self.__class__.__name__, self._code, self._detail)

    def __repr__(self):
        return "{} (status_code={}, details={})".format(self.__class__.__name__, self._code, self._detail)

    def get_status(self):
        return self._code

    def get_details(self):
        return self._detail

class JunctionPlanIntergreenValue(EmbeddedDocument):
    phfrom = IntField(min_value=1, required=True)
    phto = IntField(min_value=1, required=True)
    value = IntField(min_value=0, required=True)

class JunctionPlanPhaseValue(EmbeddedDocument):
    phid = StringField(regex=r'^\d{1,4}!?$', required=True)
    value = IntField(min_value=0, required=True)

class JunctionPlan(EmbeddedDocument):
    plid = IntField(min_value=1, required=True)
    cycle = IntField(min_value=1, required=True)
    # TODO: Make all of this fields requiered
    phase_start = EmbeddedDocumentListField(JunctionPlanPhaseValue) #, required=True)
    vehicle_intergreen = EmbeddedDocumentListField(JunctionPlanIntergreenValue) #, required=True)
    green_start = EmbeddedDocumentListField(JunctionPlanPhaseValue) #, required=True)
    vehicle_green = EmbeddedDocumentListField(JunctionPlanPhaseValue) #, required=True)
    pedestrian_green = EmbeddedDocumentListField(JunctionPlanPhaseValue) #, required=True)
    pedestrian_intergreen = EmbeddedDocumentListField(JunctionPlanIntergreenValue) #, required=True)
    system_start = EmbeddedDocumentListField(JunctionPlanPhaseValue, required=True)

class JunctionMeta(EmbeddedDocument):
    location = PointField(required=True)
    sales_id = IntField(min_value=0, required=True) # This field cannot be unique, the hash function collides in f(J001121) and f(J001122)!!
    address_reference = StringField()

class Junction(Document):
    meta = {'collection': 'Junction'}
    version = StringField(choices=['base', 'latest'], required=True, default='base')
    jid = StringField(regex=r'J\d{6}', min_length=7, max_length=7, required=True, unique=True, unique_with='version')
    metadata = EmbeddedDocumentField(JunctionMeta, required=True)
    plans = EmbeddedDocumentListField(JunctionPlan)

# External Company Model ====

class ExternalCompany(Document):
    meta = {'collection': 'ExternalCompany'}
    name = StringField(min_length=2, required=True, unique=True)

class Commune(Document):
    meta = {'collection': 'Commune'}
    maintainer = ReferenceField(ExternalCompany)
    name = StringField(unique=True)

class HeaderItem(EmbeddedDocument):
    hal = IntField(min_value=0)
    led = IntField(min_value=0)
    type = StringField(choices=[
        'L1', 'L2A', 'L2B', 'L2C', 'LD', 'L3A', 'L3B',
        'L3C', 'L4A', 'L4B', 'L4C', 'L5', 'L6',
        'L7 Peatonal', 'L8 Biciclos', 'L9 Buses', 'L10 Repetidora'
    ])

class UPS(EmbeddedDocument):
    brand = StringField()
    model = StringField()
    serial = StringField()
    capacity = StringField() #TODO: preguntar unidad de medida
    charge_duration = StringField() #TODO: preguntar unidad de medida

class Poles(EmbeddedDocument):
    hooks = IntField(min_value=0)
    vehicular = IntField(min_value=0)
    pedestrian = IntField(min_value=0)

# User Model ====

class User(Document): 
    meta = {'collection': 'User'}
    is_admin = BooleanField(default=False)
    full_name = StringField(min_length=5, required=True)
    email = EmailField(required=True, unique=True)
    rol = StringField(choices=['Empresa', 'Personal UOCT'], required=True)
    area = StringField(choices=['Sala de Control', 'Ingeniería', 'TIC', 'Mantenedora', 'Contratista', 'Administración'], required=True)
    company = ReferenceField(ExternalCompany)

# Comment Model ====

class Comment(EmbeddedDocument):
    date = DateTimeField(default=datetime.utcnow, required=True)
    message = StringField(required=True)
    author = ReferenceField(User, required=True)

class ProjectMeta(EmbeddedDocument):
    version = StringField(choices=['base', 'latest'], required=True, default='base')
    status = StringField(choices=['NEW', 'UPDATE', 'REJECTED', 'APPROVED', 'SYSTEM'], required=True) 
    status_date = DateTimeField(default=datetime.utcnow, required=True)
    status_user = ReferenceField(User, required=True)
    installation_date = DateTimeField() # PDF
    installation_company = ReferenceField(ExternalCompany)
    maintainer = ReferenceField(ExternalCompany)
    commune = StringField()
    region = StringField(default='Metropolitana', required=True)
    img = FileField() # PDF
    pdf_data = FileField() # PDF
    pedestrian_demand = BooleanField() # PDF
    pedestrian_facility = BooleanField() # PDF
    local_detector = BooleanField() # PDF
    scoot_detector = BooleanField() # PDF

# OTU Controller Model ====

class ControllerModel(Document):
    meta = {'collection': 'ControllerModel'}
    company = ReferenceField(ExternalCompany, required=True)
    model = StringField(required=True)
    firmware_version = StringField(required=True, default='Desconocido')
    checksum = StringField(required=True, default='Desconocido')
    date = DateTimeField(default=datetime.utcnow)

class Controller(EmbeddedDocument):
    meta = {'collection': 'Controller'}
    address_reference = StringField() # PDF
    gps = BooleanField() # PDF
    model = ReferenceField(ControllerModel)

# OTU Model ====

class OTUProgramItem(EmbeddedDocument):
    day = StringField(choices=['L', 'V', 'S', 'D'], required=True)
    time = StringField(regex=r'\d\d:\d\d', max_length=5, min_length=5, required=True)
    plan = StringField(max_length=2, required=True)

class OTUStagesItem(EmbeddedDocument):
    stid = StringField(regex=r'[A-Z]', max_length=1, required=True)
    type = StringField(choices=['Vehicular', 'Peatonal', 'Flecha Verde', 'Ciclista', 'No Configurada'], required=True)

class OTUPhasesItem(EmbeddedDocument):
    phid = IntField(min_value=1, required=True)
    stages = EmbeddedDocumentListField(OTUStagesItem, required=True) # TODO: validate sid unique in the list

class OTUSequenceItem(EmbeddedDocument):
    seqid = IntField(min_value=1, required=True)
    phases = EmbeddedDocumentListField(OTUPhasesItem, required=True)

class OTUMeta(EmbeddedDocument):
    serial = StringField() # PDF
    ip_address = StringField()
    netmask = StringField() # PDF
    control = IntField() # PDF
    answer = IntField() # PDF
    link_type = StringField(choices=['Digital', 'Analogo']) # PDF
    link_owner = StringField(choices=['Propio', 'Compartido']) # PDF

class OTU(Document):
    meta = {'collection': 'OTU'}
    oid = StringField(regex=r'X\d{5}0', min_length=7, max_length=7, required=True, unique=True, unique_with='version')
    version = StringField(choices=['base', 'latest'], required=True, default='base')
    metadata = EmbeddedDocumentField(OTUMeta)
    program = EmbeddedDocumentListField(OTUProgramItem) # PDF
    sequences = EmbeddedDocumentListField(OTUSequenceItem) # PDF
    intergreens = ListField(IntField(min_value=0)) # PDF # This is in row major oder, TODO: check size has square root (should be a n*n matrix)
    junctions = ListField(ReferenceField(Junction))#, required=True)   

# JsonPatch changes Model ====

class ChangeSet(Document):
    meta = {'collection': 'ChangeSets'}
    apply_to = GenericReferenceField(choices=[OTU, Junction], required=True)
    apply_to_id = StringField(regex=r'(X\d{5}0|J\d{6})', min_length=7, max_length=7, required=True)
    date = DateTimeField(default=datetime.utcnow, required=True)
    changes = ListField(DictField(), required=True)
    message = StringField()

    def __clean_special_chars_patch(self):
        self.changes = json.loads(json.dumps(self.changes).replace('$', '%$'))

    def save(self):
        self.__clean_special_chars_patch()
        return super(ChangeSet, self).save()

class ActionsLog(Document):
    meta = {'collection': 'ActionsLog'}
    user = StringField(max_length=120, required=True)
    context = StringField(max_length=120, required=True)
    action = StringField(required=True)
    origin = StringField(max_length=120, required=True)
    date = DateTimeField(default=datetime.now)

class Project(Document):
    meta = {'collection': 'Project'}
    metadata = EmbeddedDocumentField(ProjectMeta, required=True)
    oid = StringField(regex=r'X\d{5}0', min_length=7, max_length=7, required=True, unique=True, unique_with='metadata.version')
    otu = ReferenceField(OTU, required=True)
    controller = EmbeddedDocumentField(Controller)
    headers = EmbeddedDocumentListField(HeaderItem) # PDF
    ups = EmbeddedDocumentField(UPS) # PDF
    poles = EmbeddedDocumentField(Poles) # PDF
    observations = EmbeddedDocumentListField(Comment) # PDF

    # BUG: mongoengine still don't support ACID-Transactions. See https://github.com/MongoEngine/mongoengine/issues/1839
    def save_with_transaction(self):
        try:
            with get_connection().start_session() as sess:
                with sess.start_transaction():
                    saved_juncs = Junction._get_collection().insert_many([x.to_mongo() for x in self.otu.junctions], session=sess)
                    self.otu.junctions = saved_juncs.inserted_ids
                    saved_otu = OTU._get_collection().insert_one(self.otu.to_mongo(), session=sess)
                    self.oid = self.otu.oid
                    self.otu = saved_otu.inserted_id
                    saved_proj = Project._get_collection().insert_one(self.to_mongo(), session=sess)
                    self['id'] = saved_proj.inserted_id
                    self.validate()
        except (NotUniqueError, DuplicateKeyError, ValidationError) as err:
            raise DACoTBackendException(status_code=422, details='Error at Project.save_with_transaction: {}'.format(err))
        return self

class PlanParseFailedMessage(Document):
    meta = {'collection': 'PlanParseFailedMessage'}
    date = DateTimeField(default=datetime.now, required=True)
    plans = ListField(StringField(), required=True)
    message = EmbeddedDocumentField(Comment, required=True)
