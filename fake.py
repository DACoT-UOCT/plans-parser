from models import *
from mongoengine import connect
connect(host='mongodb://127.0.0.1/dacot-testing')

otu = OTU.objects(oid='X001110', version='latest').first()
sequence = [
    OTUSequenceItem(seqid=1, phases=[
        OTUPhasesItem(phid=1, stages=[OTUStagesItem(stid='A', type='Vehicular'), OTUStagesItem(stid='C', type='Vehicular'), OTUStagesItem(stid='D', type='Peatonal')]),
        OTUPhasesItem(phid=2, stages=[OTUStagesItem(stid='A', type='Vehicular'), OTUStagesItem(stid='B', type='Peatonal'), OTUStagesItem(stid='D', type='Peatonal')]),
        OTUPhasesItem(phid=3, stages=[OTUStagesItem(stid='E', type='Vehicular'), OTUStagesItem(stid='F', type='Peatonal')])
    ]),
    OTUSequenceItem(seqid=2, phases=[
        OTUPhasesItem(phid=4, stages=[OTUStagesItem(stid='H', type='Peatonal')]),
        OTUPhasesItem(phid=5, stages=[OTUStagesItem(stid='G', type='Vehicular')])
    ]),
]
intergreens = [
    0, 0, 0, 0, 4, 4, 0, 0,
    0, 0, 9, 0, 9, 0, 0, 0,
    0, 4, 0, 0, 4, 4, 0, 0,
    0, 0, 0, 0, 9, 0, 0, 0,
    4, 4, 4, 4, 0, 0, 0, 0,
    14, 0, 14, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 7,
    0, 0, 0, 0, 0, 0, 7, 0
]
otu.sequences = sequence
otu.intergreens = intergreens
otu.validate()
print(otu.to_mongo().to_dict())
otu.save()