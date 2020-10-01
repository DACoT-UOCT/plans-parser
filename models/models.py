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
    location = PointField()
    sales_id = IntField(min_value=0)
    first_access = StringField()
    second_access = StringField()
    address_reference = StringField()

class Junction(Document):
    meta = {'collection': 'Junction'}
    jid = StringField(regex=r'J\d{6}', min_length=7, max_length=7, required=True, unique=True)
    metadata = EmbeddedDocumentField(JunctionMeta, required=True)
    plans = EmbeddedDocumentListField(JunctionPlan, required=True)
    
# FasesItem ====

class FasesItem(EmbeddedDocument):
    etapas = ListField(StringField())
    imagen =StringField()

# External Company Model ====

class ExternalCompany(Document):
    meta = {'collection': 'ExternalCompany'}
    name = StringField(min_length=2, required=True, unique=True)
    
# Header Type  ====

class HeaderType(EmbeddedDocument):
    hal = IntField()
    led = IntField()

# User Model ====

class UOCTUser(Document): #TODO: add is_admin flag #TODO: add roles
    meta = {'collection': 'UOCTUser'}
    is_admin = BooleanField(default=False)
    full_name = StringField(min_length=5, required=True)
    email = EmailField(required=True, unique=True)
    rol = StringField(choices=['Empresa', 'Personal UOCT'], required=True)
    area = StringField(choices=['Sala de Control', 'Ingiería', 'TIC', 'Mantenedora', 'Contratista', 'Administración'])
    
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
    address_reference = StringField()
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
    imagen = FileField()

class OTUSequenceItem(EmbeddedDocument):
    seqid = StringField() #Después del Sprint1 cambiar a ---> IntField(min_value=1, required=True)
    fases = EmbeddedDocumentListField(OTUPhasesItem) #Después del Sprint1 cambiar a ---> , required=True)

class OTUUPS(EmbeddedDocument):
    marca = StringField()
    modelo = StringField()
    n_serie = StringField()
    capacidad = StringField()
    duracion_carga = StringField()
    
class OTUPoles(EmbeddedDocument):
    ganchos = IntField()
    vehiculares = IntField()
    peatonales = IntField()
    
class OTUHeaders(EmbeddedDocument):
    l1 = EmbeddedDocumentField(HeaderType, required=True)
    l2 = EmbeddedDocumentField(HeaderType, required=True)
    l3_l4 = EmbeddedDocumentField(HeaderType, required=True)
    l5 = EmbeddedDocumentField(HeaderType, required=True)
    l6 = EmbeddedDocumentField(HeaderType, required=True)
    peatonal = EmbeddedDocumentField(HeaderType, required=True)

class OTUMeta(EmbeddedDocument):
    version = StringField(choices=['base', 'latest'], required=True)
    maintainer = ReferenceField(ExternalCompany)
    status = StringField(choices=['NEW', 'UPDATE', 'REJECTED', 'APPROVED', 'SYSTEM'], required=True)
    status_date = DateTimeField(default=datetime.utcnow, required=True)
    status_user = ReferenceField(UOCTUser, required=True)
    installation_date = DateTimeField(default=datetime.utcnow, required=True)
    commune = StringField()
    region = StringField()
    controller = ReferenceField(OTUController)
    observations = EmbeddedDocumentListField(Comment) # Comment returned should only send message
    imgs = StringField() # TODO: Sprint1 only one image ## Se cambió a tipo string para Sprint1, inicialmente: ListField(FileField()) 
    pdf_data = StringField() 
    location = PointField()
    address_reference =  StringField()
    serial = StringField()
    ip_address = StringField()
    netmask = StringField()
    control = IntField()
    answer = IntField()
    demanda_peatonal = BooleanField(default=False)
    facilidad_peatonal =BooleanField(default=False)
    detector_local = BooleanField(default=False)
    detector_scoot = BooleanField(default=False)
    link_type = StringField(choices=['Digital', 'Analogo'], required=True)
    link_owner = StringField(choices=['Propio', 'Compartido'], required=True)
    # // NODO CONCENTRADOR?


class OTU(Document):
    meta = {'collection': 'OTU'}
    oid = StringField(regex=r'X\d{5}0', min_length=7, max_length=7, required=True, unique=True, unique_with='metadata.version')
    metadata = EmbeddedDocumentField(OTUMeta, required=True)
    program = EmbeddedDocumentListField(OTUProgramItem, required=True)
    secuencias = EmbeddedDocumentListField(OTUSequenceItem) #, required=True)
    entreverdes = ListField(IntField(min_value=0)) #, required=True)) # This is in row major oder, TODO: check size has square root (should be a n*n matrix)
    junctions = ListField(ReferenceField(Junction), required=True)
    ups = EmbeddedDocumentField(OTUUPS) #, required=True) # TODO: change to english for next sprint.
    postes = EmbeddedDocumentField(OTUPoles) #, required=True)
    cabezales = EmbeddedDocumentField(OTUHeaders) #, required=True)
    


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
    secuencias = EmbeddedDocumentListField(OTUSequenceItem) #, required=True)
    entreverdes = ListField(IntField(min_value=0)) #, required=True)) # This is in row major oder, TODO: check size has square root (should be a n*n matrix)
    junctions = ListField(ReferenceField(Junction), required=True)
    ups = EmbeddedDocumentField(OTUUPS) #, required=True) # TODO: change to english for next sprint.
    postes = EmbeddedDocumentField(OTUPoles) #, required=True)
    cabezales = EmbeddedDocumentField(OTUHeaders) #, required=True)
    fases = EmbeddedDocumentListField(FasesItem)
    stages = ListField(ListField())
    
    #date_modified = DateTimeField(default=datetime.now)
