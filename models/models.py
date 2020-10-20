import json
from mongoengine import EmbeddedDocument, IntField, EmbeddedDocumentListField
from mongoengine import Document, PointField, StringField, ListField, DateTimeField
from mongoengine import EmbeddedDocumentField, EmailField, FileField, LongField, ReferenceField
from mongoengine import GenericReferenceField, DictField, BooleanField

from datetime import datetime

# Junction Model ====

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
    # sales_id = IntField(min_value=0)
    # first_access = StringField(required=True)
    # second_access = StringField(required=True)
    address_reference = StringField()

class Junction(Document):
    meta = {'collection': 'Junction'}
    jid = StringField(regex=r'J\d{6}', min_length=7, max_length=7, required=True, unique=True)
    metadata = EmbeddedDocumentField(JunctionMeta, required=True)
    plans = EmbeddedDocumentListField(JunctionPlan)

# External Company Model ====

class ExternalCompany(Document):
    meta = {'collection': 'ExternalCompany'}
    name = StringField(min_length=2, required=True, unique=True)

class Commune(Document):
    meta = {'collection': 'Commune'}
    maintainer = ReferenceField(ExternalCompany)
    name = StringField()

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
    area = StringField(choices=['Sala de Control', 'Ingiería', 'TIC', 'Mantenedora', 'Contratista', 'Administración'], required=True)
    company = ReferenceField(ExternalCompany)

# Comment Model ====

class Comment(EmbeddedDocument):
    date = DateTimeField(default=datetime.utcnow, required=True)
    message = StringField(max_length=255, required=True)
    author = ReferenceField(User, required=True)

class ProjectMeta(EmbeddedDocument):
    version = StringField(choices=['base', 'latest'], required=True)
    maintainer = ReferenceField(ExternalCompany) 
    status = StringField(choices=['NEW', 'UPDATE', 'REJECTED', 'APPROVED', 'SYSTEM'], required=True) 
    status_date = DateTimeField(default=datetime.utcnow, required=True)
    status_user = ReferenceField(User, required=True)
    installation_date = DateTimeField(default=datetime.utcnow, required=True)
    commune = StringField()
    region = StringField()
    img = FileField()
    pdf_data = FileField()
    pedestrian_demand = BooleanField(default=False)
    pedestrian_facility = BooleanField(default=False)
    local_detector = BooleanField(default=False)
    scoot_detector = BooleanField(default=False)

# OTU Controller Model ====

class ControllerModel(Document):
    meta = {'collection': 'ControllerModel'}
    company = ReferenceField(ExternalCompany, required=True)
    model = StringField(required=True)
    firmware_version = StringField(required=True)
    checksum = StringField(required=True)
    date = DateTimeField(default=datetime.utcnow)

class Controller(EmbeddedDocument):
    meta = {'collection': 'Controller'}
    address_reference = StringField()
    gps = BooleanField()
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
    serial = StringField() 
    ip_address = StringField() 
    netmask = StringField() 
    control = IntField()
    answer = IntField()
    link_type = StringField(choices=['Digital', 'Analogo'], required=True)
    link_owner = StringField(choices=['Propio', 'Compartido'], required=True)

class OTU(Document):
    meta = {'collection': 'OTU'}
    oid = StringField(regex=r'X\d{5}0', min_length=7, max_length=7, required=True, unique=True)# TODO:, unique_with='metadata.version')
    metadata = EmbeddedDocumentField(OTUMeta, required=True)
    program = EmbeddedDocumentListField(OTUProgramItem) #, required=True)
    sequences = EmbeddedDocumentListField(OTUSequenceItem) #, required=True)
    intergreens = ListField(IntField(min_value=0)) #, required=True)) # This is in row major oder, TODO: check size has square root (should be a n*n matrix)
    junctions = ListField(ReferenceField(Junction), required=True)   

# JsonPatch changes Model ====

class ChangeSet(Document):
    meta = {'collection': 'ChangeSets'}
    apply_to = GenericReferenceField(choices=[OTU, Junction], required=True)
    date = DateTimeField(default=datetime.utcnow, required=True)
    changes = ListField(DictField(), required=True)

    def __clean_special_chars_patch(self):
        self.changes = json.loads(json.dumps(self.changes).replace('$', '%$'))

    def save(self):
        self.__clean_special_chars_patch()
        return super(ChangeSet, self).save()

class History(Document):
    meta = {'collection': 'History'}
    user = StringField(max_length=200, required=True)
    context = StringField(max_length=200, required=True)
    action = StringField(max_length=200, required=True)
    origin = StringField(max_length=200, required=True)
    date = DateTimeField(default=datetime.now)

class Project(Document):
    meta = {'collection': 'Project'}
    metadata = EmbeddedDocumentField(ProjectMeta, required=True)
    otu = ReferenceField(OTU, required=True, unique=True)
    controller = EmbeddedDocumentField(Controller)
    headers = EmbeddedDocumentListField(HeaderItem)
    ups = EmbeddedDocumentField(UPS)
    poles = EmbeddedDocumentField(Poles)
    observations = EmbeddedDocumentListField(Comment)
