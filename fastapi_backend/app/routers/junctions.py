from fastapi import APIRouter, Body, Path, HTTPException, BackgroundTasks
from pydantic import BaseModel
from ..models import Junction
from .actions_log import register_action
import json
from mongoengine.errors import ValidationError
router = APIRouter()

@router.get('/junctions/{jid}', status_code=200)
async def read_junction(background_tasks: BackgroundTasks, jid: str = Path(..., min_length=7, max_length=7, regex=r'J\d{6}')):
    junction = Junction.objects(jid=jid).exclude('id').first()
    if junction:
        register_action('Desconocido', 'Junctions', 'Un usuario ha obtenido la junction {} correctamente'.format(jid), background=background_tasks)
        return junction.to_mongo().to_dict()
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
