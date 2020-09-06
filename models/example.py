import os
import json
import jsonpatch

from mongoengine import connect

from models import Junction, JunctionPlan, JunctionPlanPhaseValue, JunctionPlanIntergreenValue, JunctionMeta
from models import OTU, OTUProgramItem, OTUSequenceItem, OTUPhasesItem, OTUStagesItem, OTUMeta
from models import ExternalCompany, UOCTUser, ChangeSet

connect('dacot-dev', host=os.environ['MONGO_URI'])

# Drop existing data

Junction.drop_collection()
UOCTUser.drop_collection()
OTU.drop_collection()


# data for J001331

j1 = Junction(jid='J001331', plans=[
    JunctionPlan(plid=3, cycle=110, phase_start=[
        JunctionPlanPhaseValue(phid=1, value=82),
        JunctionPlanPhaseValue(phid=2, value=6),
        JunctionPlanPhaseValue(phid=3, value=30)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=4),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=4),
    ], green_start=[
        JunctionPlanPhaseValue(phid=1, value=86),
        JunctionPlanPhaseValue(phid=2, value=10),
        JunctionPlanPhaseValue(phid=3, value=34)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=1, value=30),
        JunctionPlanPhaseValue(phid=2, value=20),
        JunctionPlanPhaseValue(phid=3, value=48)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=1, value=30),
        JunctionPlanPhaseValue(phid=2, value=15),
        JunctionPlanPhaseValue(phid=3, value=38)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=14),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=9),
    ], system_start=[
        JunctionPlanPhaseValue(phid=1, value=72),
        JunctionPlanPhaseValue(phid=2, value=6),
        JunctionPlanPhaseValue(phid=3, value=25)
    ]), 
    JunctionPlan(plid=4, cycle=120, phase_start=[
        JunctionPlanPhaseValue(phid=1, value=59),
        JunctionPlanPhaseValue(phid=2, value=94),
        JunctionPlanPhaseValue(phid=3, value=118)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=4),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=4),
    ], green_start=[
        JunctionPlanPhaseValue(phid=1, value=63),
        JunctionPlanPhaseValue(phid=2, value=98),
        JunctionPlanPhaseValue(phid=3, value=2)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=1, value=31),
        JunctionPlanPhaseValue(phid=2, value=20),
        JunctionPlanPhaseValue(phid=3, value=57)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=1, value=31),
        JunctionPlanPhaseValue(phid=2, value=15),
        JunctionPlanPhaseValue(phid=3, value=47)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=14),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=9),
    ], system_start=[
        JunctionPlanPhaseValue(phid=1, value=49),
        JunctionPlanPhaseValue(phid=2, value=94),
        JunctionPlanPhaseValue(phid=3, value=113)
    ]), 
    JunctionPlan(plid=5, cycle=90, phase_start=[
        JunctionPlanPhaseValue(phid=1, value=83),
        JunctionPlanPhaseValue(phid=2, value=21),
        JunctionPlanPhaseValue(phid=3, value=41)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=4),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=4),
    ], green_start=[
        JunctionPlanPhaseValue(phid=1, value=87),
        JunctionPlanPhaseValue(phid=2, value=25),
        JunctionPlanPhaseValue(phid=3, value=45)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=1, value=24),
        JunctionPlanPhaseValue(phid=2, value=16),
        JunctionPlanPhaseValue(phid=3, value=38)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=1, value=24),
        JunctionPlanPhaseValue(phid=2, value=11),
        JunctionPlanPhaseValue(phid=3, value=28)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=14),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=9),
    ], system_start=[
        JunctionPlanPhaseValue(phid=1, value=73),
        JunctionPlanPhaseValue(phid=2, value=21),
        JunctionPlanPhaseValue(phid=3, value=36)
    ]), 
    JunctionPlan(plid=6, cycle=72, phase_start=[
        JunctionPlanPhaseValue(phid=1, value=11),
        JunctionPlanPhaseValue(phid=2, value=21),
        JunctionPlanPhaseValue(phid=3, value=59)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=4),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=4),
    ], green_start=[
        JunctionPlanPhaseValue(phid=1, value=15),
        JunctionPlanPhaseValue(phid=2, value=25),
        JunctionPlanPhaseValue(phid=3, value=63)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=1, value=6),
        JunctionPlanPhaseValue(phid=2, value=34),
        JunctionPlanPhaseValue(phid=3, value=20)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=1, value=6),
        JunctionPlanPhaseValue(phid=2, value=29),
        JunctionPlanPhaseValue(phid=3, value=10)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=14),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=9),
    ], system_start=[
        JunctionPlanPhaseValue(phid=1, value=1),
        JunctionPlanPhaseValue(phid=2, value=21),
        JunctionPlanPhaseValue(phid=3, value=54)
    ]), 
    JunctionPlan(plid=8, cycle=120, phase_start=[
        JunctionPlanPhaseValue(phid=1, value=23),
        JunctionPlanPhaseValue(phid=2, value=66),
        JunctionPlanPhaseValue(phid=3, value=90)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=4),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=4),
    ], green_start=[
        JunctionPlanPhaseValue(phid=1, value=27),
        JunctionPlanPhaseValue(phid=2, value=70),
        JunctionPlanPhaseValue(phid=3, value=94)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=1, value=39),
        JunctionPlanPhaseValue(phid=2, value=20),
        JunctionPlanPhaseValue(phid=3, value=49)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=1, value=39),
        JunctionPlanPhaseValue(phid=2, value=15),
        JunctionPlanPhaseValue(phid=3, value=39)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=14),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=9),
    ], system_start=[
        JunctionPlanPhaseValue(phid=1, value=13),
        JunctionPlanPhaseValue(phid=2, value=66),
        JunctionPlanPhaseValue(phid=3, value=85)
    ]), 
    JunctionPlan(plid=28, cycle=120, phase_start=[
        JunctionPlanPhaseValue(phid=1, value=23),
        JunctionPlanPhaseValue(phid=2, value=66),
        JunctionPlanPhaseValue(phid=3, value=90)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=4),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=4),
    ], green_start=[
        JunctionPlanPhaseValue(phid=1, value=27),
        JunctionPlanPhaseValue(phid=2, value=70),
        JunctionPlanPhaseValue(phid=3, value=94)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=1, value=39),
        JunctionPlanPhaseValue(phid=2, value=20),
        JunctionPlanPhaseValue(phid=3, value=49)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=1, value=39),
        JunctionPlanPhaseValue(phid=2, value=15),
        JunctionPlanPhaseValue(phid=3, value=39)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=3, phto=1, value=14),
        JunctionPlanIntergreenValue(phfrom=1, phto=2, value=4),
        JunctionPlanIntergreenValue(phfrom=2, phto=3, value=9),
    ], system_start=[
        JunctionPlanPhaseValue(phid=1, value=13),
        JunctionPlanPhaseValue(phid=2, value=66),
        JunctionPlanPhaseValue(phid=3, value=85)
    ])
], metadata=JunctionMeta(location=(-33.4187140, -70.6027238)))

j1.validate()

# data for J001332

j2 = Junction(jid='J001332', plans=[
    JunctionPlan(plid=3, cycle=55, phase_start=[
        JunctionPlanPhaseValue(phid=4, value=14),
        JunctionPlanPhaseValue(phid=5, value=30)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], green_start=[
        JunctionPlanPhaseValue(phid=4, value=18),
        JunctionPlanPhaseValue(phid=5, value=37)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=4, value=12),
        JunctionPlanPhaseValue(phid=5, value=32)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=4, value=12),
        JunctionPlanPhaseValue(phid=5, value=32)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], system_start=[
        JunctionPlanPhaseValue(phid=4, value=14),
        JunctionPlanPhaseValue(phid=5, value=30)
    ]),
    JunctionPlan(plid=4, cycle=120, phase_start=[
        JunctionPlanPhaseValue(phid=4, value=94),
        JunctionPlanPhaseValue(phid=5, value=113)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], green_start=[
        JunctionPlanPhaseValue(phid=4, value=98),
        JunctionPlanPhaseValue(phid=5, value=0)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=4, value=15),
        JunctionPlanPhaseValue(phid=5, value=94)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=4, value=15),
        JunctionPlanPhaseValue(phid=5, value=94)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], system_start=[
        JunctionPlanPhaseValue(phid=4, value=94),
        JunctionPlanPhaseValue(phid=5, value=113)
    ]),
    JunctionPlan(plid=5, cycle=90, phase_start=[
        JunctionPlanPhaseValue(phid=4, value=22),
        JunctionPlanPhaseValue(phid=5, value=41)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], green_start=[
        JunctionPlanPhaseValue(phid=4, value=26),
        JunctionPlanPhaseValue(phid=5, value=48)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=4, value=15),
        JunctionPlanPhaseValue(phid=5, value=64)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=4, value=15),
        JunctionPlanPhaseValue(phid=5, value=64)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], system_start=[
        JunctionPlanPhaseValue(phid=4, value=22),
        JunctionPlanPhaseValue(phid=5, value=41)
    ]),
    JunctionPlan(plid=6, cycle=72, phase_start=[
        JunctionPlanPhaseValue(phid=4, value=22),
        JunctionPlanPhaseValue(phid=5, value=49)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], green_start=[
        JunctionPlanPhaseValue(phid=4, value=26),
        JunctionPlanPhaseValue(phid=5, value=56)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=4, value=23),
        JunctionPlanPhaseValue(phid=5, value=38)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=4, value=23),
        JunctionPlanPhaseValue(phid=5, value=38)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], system_start=[
        JunctionPlanPhaseValue(phid=4, value=22),
        JunctionPlanPhaseValue(phid=5, value=49)
    ]),
    JunctionPlan(plid=8, cycle=120, phase_start=[
        JunctionPlanPhaseValue(phid=4, value=8),
        JunctionPlanPhaseValue(phid=5, value=27)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], green_start=[
        JunctionPlanPhaseValue(phid=4, value=12),
        JunctionPlanPhaseValue(phid=5, value=34)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=4, value=15),
        JunctionPlanPhaseValue(phid=5, value=94)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=4, value=15),
        JunctionPlanPhaseValue(phid=5, value=94)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], system_start=[
        JunctionPlanPhaseValue(phid=4, value=8),
        JunctionPlanPhaseValue(phid=5, value=27)
    ]),
    JunctionPlan(plid=28, cycle=120, phase_start=[
        JunctionPlanPhaseValue(phid=4, value=8),
        JunctionPlanPhaseValue(phid=5, value=27)
    ], vehicle_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], green_start=[
        JunctionPlanPhaseValue(phid=4, value=12),
        JunctionPlanPhaseValue(phid=5, value=34)
    ], vehicle_green=[
        JunctionPlanPhaseValue(phid=4, value=15),
        JunctionPlanPhaseValue(phid=5, value=94)
    ], pedestrian_green=[
        JunctionPlanPhaseValue(phid=4, value=15),
        JunctionPlanPhaseValue(phid=5, value=94)
    ], pedestrian_intergreen=[
        JunctionPlanIntergreenValue(phfrom=4, phto=5, value=7),
        JunctionPlanIntergreenValue(phfrom=5, phto=4, value=4)
    ], system_start=[
        JunctionPlanPhaseValue(phid=4, value=8),
        JunctionPlanPhaseValue(phid=5, value=27)
    ])
], metadata=JunctionMeta(location=(-33.4183259, -70.6029155)))

j2.validate()

j1 = j1.save().reload()
j2 = j2.save().reload()

# data for X001330

programs = [
    OTUProgramItem(day='L', time='00:01', plan='S'), OTUProgramItem(day='L', time='00:01', plan='6'),
    OTUProgramItem(day='L', time='07:00', plan='XS'), OTUProgramItem(day='L', time='07:00', plan='28'),
    OTUProgramItem(day='L', time='07:30', plan='28'), OTUProgramItem(day='L', time='10:00', plan='S'),
    OTUProgramItem(day='L', time='10:00', plan='3'), OTUProgramItem(day='L', time='12:00', plan='8'),
    OTUProgramItem(day='L', time='14:30', plan='3'), OTUProgramItem(day='L', time='17:00', plan='XS'),
    OTUProgramItem(day='L', time='17:00', plan='4'), OTUProgramItem(day='L', time='20:30', plan='S'),
    OTUProgramItem(day='L', time='21:00', plan='5'), OTUProgramItem(day='L', time='22:00', plan='6'),
    OTUProgramItem(day='V', time='00:01', plan='S'), OTUProgramItem(day='V', time='00:01', plan='6'),
    OTUProgramItem(day='V', time='07:00', plan='XS'), OTUProgramItem(day='V', time='07:00', plan='28'),
    OTUProgramItem(day='V', time='07:30', plan='28'), OTUProgramItem(day='V', time='10:00', plan='S'),
    OTUProgramItem(day='V', time='10:00', plan='3'), OTUProgramItem(day='V', time='12:00', plan='8'),
    OTUProgramItem(day='V', time='14:30', plan='3'), OTUProgramItem(day='V', time='17:00', plan='XS'),
    OTUProgramItem(day='V', time='17:00', plan='4'), OTUProgramItem(day='V', time='20:30', plan='S'),
    OTUProgramItem(day='V', time='21:00', plan='5'), OTUProgramItem(day='V', time='22:00', plan='6'),
    OTUProgramItem(day='S', time='00:01', plan='S'), OTUProgramItem(day='S', time='00:01', plan='6'),
    OTUProgramItem(day='S', time='10:00', plan='5'), OTUProgramItem(day='S', time='14:00', plan='6'),
    OTUProgramItem(day='D', time='00:01', plan='S'), OTUProgramItem(day='D', time='00:01', plan='6'),
    OTUProgramItem(day='D', time='10:00', plan='5'), OTUProgramItem(day='D', time='14:00', plan='6')
]
sequence = [
    OTUSequenceItem(seqid=1, phases=[
        OTUPhasesItem(phid=1, stages=[OTUStagesItem(stid='A', type='VEHI'), OTUStagesItem(stid='C', type='VEHI'), OTUStagesItem(stid='D', type='PEAT')]),
        OTUPhasesItem(phid=2, stages=[OTUStagesItem(stid='A', type='VEHI'), OTUStagesItem(stid='B', type='PEAT'), OTUStagesItem(stid='D', type='PEAT')]),
        OTUPhasesItem(phid=3, stages=[OTUStagesItem(stid='E', type='VEHI'), OTUStagesItem(stid='F', type='PEAT')])
    ]),
    OTUSequenceItem(seqid=2, phases=[
        OTUPhasesItem(phid=4, stages=[OTUStagesItem(stid='H', type='PEAT')]),
        OTUPhasesItem(phid=5, stages=[OTUStagesItem(stid='G', type='VEHI')])
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

# OTU Meta

auter = ExternalCompany(name='Auter SPA')

cponce = UOCTUser(uid=10, full_name='Carlos Andres Ponce Godoy', email='cponce@gmail.com', area='TIC', rut='19664296-K')
cponce = cponce.save().reload()

otu_meta = OTUMeta(version=0, installed_by=auter, maintainer=auter, status='NEW', status_user=cponce,
        location=(-33.41849, -70.603594), address='Av. Luis Thayer Ojeda 42-18', address_reference='Providencia - Luis Thayer Ojeda - Nueva Providencia',
        commune='Providencia', controller='A4F')

otu = OTU(program=programs, iid='X001330', sequence=sequence, intergreens=intergreens, metadata=otu_meta)
otu.junctions = [j1, j2]
otu.validate()
otu = otu.save().reload()

updated = otu.from_json(otu.to_json())
updated.metadata.version = updated.metadata.version + 1
updated.program[10].day = 'V'
updated.program[10].time = '33:33'
updated.program[10].plan = 'XS'
updated.metadata.observations.append('Actualizado desde Script de prueba')
updated.validate()

# This to_json() and loads() is stupid, but there is no better way to do this.
updated_dict = json.loads(updated.to_json())
otu_dict = json.loads(otu.to_json())

patch = jsonpatch.make_patch(otu_dict, updated_dict)
changeset = ChangeSet(apply_to=otu, changes=patch)
changeset.validate()

jsonpatch.apply_patch(otu_dict, patch, in_place=True)
del otu_dict['_id']
otu = OTU.from_json(json.dumps(otu_dict))
otu.validate()

changeset = changeset.save().reload()
otu = otu.save().reload()

print(changeset.to_json())

print('Done')
