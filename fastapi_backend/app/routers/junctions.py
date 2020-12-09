from fastapi import APIRouter, Body, Path, HTTPException, BackgroundTasks
from pydantic import BaseModel
from ..models import Project
from .actions_log import register_action
import json
from mongoengine.errors import ValidationError
import bson.json_util as bjson
router = APIRouter()

get_sample = bjson.dumps(Project.objects().exclude('id').first().otu.junctions[0].to_mongo(), sort_keys=True, indent=4)

@router.get('/junctions/{jid}', tags=["Junctions"], status_code=200, responses={
    404: {
        'description': 'No encontrada. La intersección con el identificador especificado no existe en la base de datos.',
        'content': {
            'application/json': {'example': {"detail": "Junction J999999 not found"}}
        }
    },
    200: {
        'description': 'OK. Se ha obtenido la intersección correctamente.',
        'content': {
            'application/json': {'example': get_sample}
        }
    }
})
async def read_junction(background_tasks: BackgroundTasks, jid: str = Path(..., min_length=7, max_length=7, regex=r'J\d{6}',
    description='Identificador único de la intersección que buscamos consultar. Debe cumplir con la expresión regular de validación.')):
    proj = Project.objects(otu__junctions__jid=jid).exclude('id').first()
    if proj:
        register_action('Desconocido', 'Junctions', 'Un usuario ha obtenido la junction {} correctamente'.format(jid), background=background_tasks)
        for junc in proj.otu.junctions:
            if junc.jid == jid:
                return junc.to_mongo().to_dict()
    else:
        register_action('Desconocido', 'Junctions', 'Un usuario ha intenado obtener la junction {}, pero no existe'.format(jid), background=background_tasks)
        raise HTTPException(status_code=404, detail='Junction {} not found'.format(jid))

# @router.post('/junctions', tags=["junctions"], status_code=201)
# async def create_junction(junction:  dict, background_tasks: BackgroundTasks):
#     a_user = "Camilo"
#     background_tasks.add_task(register_action, a_user, context="POST ",
#                               component="Sistema", origin="Create Request")
#     mongoJunction = models.Junction.from_json(json.dumps(junction))
#     print(mongoJunction)
#     try:
#         mongoJunction.validate()
#     except ValidationError as error:
#         print(error)
#         #raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "There goes my error"},)
#         return error
#     mongoJunction.save()
#     mongoJunction = mongoJunction.reload()
#     return [{"username": "Foo"}, {"username": "Bar"}]
#

@router.get('/junctions/coords', tags=["Junctions"], status_code=200, responses={
    404: {
        'description': 'No encontrada. Las coordenadas no existen en la base de datos.',
        'content': {
            'application/json': {'example': {"detail": "Coordinates not found"}}
        }
    },
    200: {
        'description': 'OK. Se han obtenido las coordenadas correctamente.',
        'content': {
            'application/json': {'example': {
        "coordinates": [
            -33.429978,
            -70.622176
        ],
        "jid": "J001111"
    }}
        }
    }
})
async def get_coords():
    all_locations = Project.objects().only('otu.junctions.jid', 'otu.junctions.metadata.location').all()
    result = []
    for proj in all_locations:
        for junc in proj.otu.junctions:
            result.append({'jid': junc.jid, 'coordinates': junc.metadata.location['coordinates']})
    return result
