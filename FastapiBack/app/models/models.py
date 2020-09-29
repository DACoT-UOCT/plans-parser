import json
from mongoengine import EmbeddedDocument, IntField, EmbeddedDocumentListField
from mongoengine import Document, PointField, StringField, ListField, DateTimeField
from mongoengine import EmbeddedDocumentField, EmailField, FileField, LongField, ReferenceField
from mongoengine import GenericReferenceField, DictField
import datetime
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
    location = PointField()
    sales_id = IntField(min_value=0)
    first_access = StringField()
    second_access = StringField()

class Junction(Document):
    meta = {'collection': 'Junction'}
    jid = StringField(regex=r'J\d{6}', min_length=7, max_length=7, required=True, unique=True)
    metadata = EmbeddedDocumentField(JunctionMeta, required=True)
    plans = EmbeddedDocumentListField(JunctionPlan, required=True)

# External Company Model ====

class ExternalCompany(Document):
    meta = {'collection': 'ExternalCompany'}
    name = StringField(min_length=2, required=True, unique=True)

# User Model ====

class UOCTUser(Document): #TODO: add is_admin flag
    meta = {'collection': 'UOCTUser'}
    uid = IntField(min_value=0, required=True, unique=True)
    full_name = StringField(min_length=5, required=True)
    email = EmailField(required=True)
    area = StringField(choices=['Sala de Control', 'Ingiería', 'TIC'], required=True)
    rut = StringField(min_length=10, required=True) # TODO: validation

# Comment Model ====

class Comment(EmbeddedDocument):
    date = DateTimeField(default=datetime.utcnow, required=True)
    message = StringField(max_length=255, required=True)
    author = ReferenceField(UOCTUser, required=True)

# OTU Controller Model ====

class OTUController(Document):
    meta = {'collection': 'OTUController'}
    company = ReferenceField(ExternalCompany, required=True, unique_with='model')
    model = StringField(required=True)
    firmware_version = StringField()#required=True)
    checksum = StringField()#required=True)
    date = DateTimeField(default=datetime.utcnow, required=True)

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
    version = StringField(choices=['base', 'latest'], required=True)
    maintainer = ReferenceField(ExternalCompany)
    status = StringField(choices=['NEW', 'UPDATE', 'REJECTED', 'APPROVED', 'SYSTEM'], required=True)
    status_date = DateTimeField(default=datetime.utcnow, required=True)
    status_user = ReferenceField(UOCTUser, required=True)
    installation_date = DateTimeField(default=datetime.utcnow, required=True)
    commune = StringField()
    controller = ReferenceField(OTUController)
    observations = EmbeddedDocumentListField(Comment)
    imgs = ListField(FileField())
    original_data = FileField()

class OTU(Document):
    meta = {'collection': 'OTU'}
    oid = StringField(regex=r'X\d{5}0', min_length=7, max_length=7, required=True, unique=True, unique_with='metadata.version')
    metadata = EmbeddedDocumentField(OTUMeta, required=True)
    program = EmbeddedDocumentListField(OTUProgramItem, required=True)
    sequence = EmbeddedDocumentListField(OTUSequenceItem) #, required=True)
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
    #{"user": user, "context": context, "component": component, "origin": origin }
    meta = {'collection': 'History'}
    user = StringField(max_length=200, required=True)
    context = StringField(max_length=200, required=True)
    component = StringField(max_length=200, required=True)
    origin = StringField(max_length=200, required=True)
    date_modified = DateTimeField(default=datetime.now)

class Request(Document):
    #{"user": user, "context": context, "component": component, "origin": origin }
    meta = {'collection': 'requests'}
    oid = StringField(regex=r'X\d{5}0', min_length=7, max_length=7, required=True, unique=True, unique_with='metadata.version')
    metadata = EmbeddedDocumentField(OTUMeta, required=True)
    program = EmbeddedDocumentListField(OTUProgramItem, required=True)
    sequence = EmbeddedDocumentListField(OTUSequenceItem) #, required=True)
    intergreens = ListField(IntField(min_value=0)) #, required=True)) # This is in row major oder, TODO: check size has square root (should be a n*n matrix)
    junctions = ListField(ReferenceField(Junction), required=True)
    #date_modified = DateTimeField(default=datetime.now)
    