from mongoengine import EmbeddedDocument, IntField, EmbeddedDocumentListField
from mongoengine import Document, PointField, StringField, ListField, DateTimeField
from mongoengine import EmbeddedDocumentField, EmailField, FileField, LongField, ReferenceField
from datetime import datetime

# Junction Model ====

class JunctionPlanIntergreenValue(EmbeddedDocument):
    phfrom = IntField(min_value=1, required=True)
    phto = IntField(min_value=1, required=True)
    value = IntField(min_value=0, required=True)

class JunctionPlanPhaseValue(EmbeddedDocument):
    phid = IntField(min_value=1, required=True)
    value = IntField(min_value=0, required=True)

class JunctionPlan(EmbeddedDocument):
    plid = IntField(min_value=1, required=True)
    cycle = IntField(min_value=1, required=True)
    phase_start = EmbeddedDocumentListField(JunctionPlanPhaseValue, required=True)
    vehicle_intergreen = EmbeddedDocumentListField(JunctionPlanIntergreenValue, required=True)
    green_start = EmbeddedDocumentListField(JunctionPlanPhaseValue, required=True)
    vehicle_green = EmbeddedDocumentListField(JunctionPlanPhaseValue, required=True)
    pedestrian_green = EmbeddedDocumentListField(JunctionPlanPhaseValue, required=True)
    pedestrian_intergreen = EmbeddedDocumentListField(JunctionPlanIntergreenValue, required=True)
    system_start = EmbeddedDocumentListField(JunctionPlanPhaseValue, required=True)

class JunctionMeta(EmbeddedDocument):
    location = PointField(required=True)

class Junction(Document):
    meta = {'collection': 'Junction'}
    jid = StringField(regex=r'J\d{6}', min_length=7, max_length=7, required=True, unique=True)
    metadata = EmbeddedDocumentField(JunctionMeta, required=True)
    plans = EmbeddedDocumentListField(JunctionPlan, required=True)

# External Company Model ====

class ExternalCompany(EmbeddedDocument):
    name = StringField(min_length=2, required=True)

# User Model ====

class UOCTUser(Document):
    meta = {'collection': 'UOCTUser'}
    uid = IntField(min_value=0, required=True, unique=True)
    full_name = StringField(min_length=5, required=True)
    email = EmailField(required=True)
    area = StringField(choices=['Sala de Control', 'Ingiería', 'TIC'], required=True)
    rut = StringField(min_length=10, required=True) # TODO: validation

# OTU Model ====

class OTUProgramItem(EmbeddedDocument):
    day = StringField(choices=['L', 'V', 'S', 'D'], required=True)
    time = StringField(regex=r'\d\d:\d\d', max_length=5, min_length=5, required=True)
    plan = StringField(max_length=2, required=True)

class OTUStagesItem(EmbeddedDocument):
    stid = StringField(regex=r'[A-Z]', max_length=1, required=True)
    type = StringField(choices=['VEHI', 'PEAT'], required=True)

class OTUPhasesItem(EmbeddedDocument):
    phid = IntField(min_value=1, required=True)
    stages = EmbeddedDocumentListField(OTUStagesItem, required=True) # TODO: validate sid unique in the list
    img = FileField()

class OTUSequenceItem(EmbeddedDocument):
    seqid = IntField(min_value=1, required=True)
    phases = EmbeddedDocumentListField(OTUPhasesItem, required=True)

class OTUMeta(EmbeddedDocument):
    version = LongField(min_value=0, required=True)
    installed_by = EmbeddedDocumentField(ExternalCompany, required=True)
    maintainer = EmbeddedDocumentField(ExternalCompany, required=True)
    status = StringField(choices=['NEW', 'UPDATE', 'REJECTED', 'APPROVED', 'SYSTEM'], required=True)
    status_date = DateTimeField(default=datetime.utcnow, required=True)
    status_user = ReferenceField(UOCTUser, required=True)
    installation_date = DateTimeField(default=datetime.utcnow, required=True)
    location = PointField(required=True)
    address = StringField(required=True)
    address_reference = StringField(required=True)
    commune = StringField(required=True)
    controller = StringField(required=True) # TODO: Make this an embedded document
    observations = ListField(StringField(max_length=255))
    imgs = ListField(FileField())
    original_data = FileField() # required=True

class OTU(Document):
    meta = {'collection': 'OTU'}
    iid = StringField(regex=r'X\d{5}0', min_length=7, max_length=7, required=True, unique=True)
    metadata = EmbeddedDocumentField(OTUMeta, required=True)
    program = EmbeddedDocumentListField(OTUProgramItem, required=True)
    sequence = EmbeddedDocumentListField(OTUSequenceItem, required=True)
    intergreens = ListField(IntField(min_value=0, required=True)) # row major oder, TODO: check size has square root (should be a n*n matrix)
    junctions = ListField(ReferenceField(Junction), required=True)
