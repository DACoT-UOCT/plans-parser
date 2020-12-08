from fastapi import APIRouter, Body, Path, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from mongoengine import EmailField
from ..models import Project
from .actions_log import register_action
import json
from mongoengine.errors import ValidationError,NotUniqueError
import bson.json_util as bjson

router = APIRouter()

get_sample = bjson.dumps(Project.objects().exclude('id').first().otu.to_mongo(), sort_keys=True, indent=4)

# @router.post('/otu',tags=["otu"],status_code=201)
# async def create_otu(otu:  dict, user: EmailStr ,background_tasks: BackgroundTasks):
#     a_user= "Camilo"
#     mongoOTU = models.OTU.from_json(json.dumps(otu))
#     print(type(mongoOTU))
#     try:
#         mongoOTU.validate()
#     except ValidationError as error:
#         print(error)
#         #raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "There goes my error"},)
#         return error
#     try:
#         mongoOTU.save()
#     except NotUniqueError:
#         #print(error)
#         raise HTTPException(status_code=409, detail="Duplicated item",headers={"X-Error": "There goes my error"},)
#     background_tasks.add_task(register_action,user,context= "Create OTU request ",component= "Sistema", origin="Web")
#     #mongoOTU = mongoOTU.reload()
#     return [{"username": "Foo"}, {"username": "Bar"}]
#
# @router.get('/otu', tags=["otu"])
# async def read_users_otu(background_tasks: BackgroundTasks, user: EmailStr):
#     a_user= "Camilo"
#     user_f = models.UOCTUser.objects(email=user).first()
#     if user_f == None:
#         raise HTTPException(status_code=404, detail="User not found",headers={"X-Error": "Usuario no encontrado"},)
#         return
#     otu_list= []
#     for otu in models.Request.objects(metadata__status= "SYSTEM",metadata__status_user= user).only('oid', 'metadata.status','metadata.status_user'):
#         otu_list.append(json.loads(otu.to_json()))
#         #print(otu.metadata.status_user.to_json())
#     background_tasks.add_task(register_action,user,context= "Request user OTUs",component= "Sistema", origin="web")
#     return otu_list

@router.get('/otu/{oid}', tags=["OTU"], responses={
    404: {
        'description': 'No encontrada. La instalación con el identificador especificado no existe en la base de datos.',
        'content': {
            'application/json': {'example': {"detail": "OTU X999990 not found"}}
        }
    },
    200: {
        'description': 'OK. Se ha obtenido la instalación correctamente.',
        'content': {
            'application/json': {'example': get_sample}
        }
    }
})
async def read_otu(background_tasks: BackgroundTasks, oid: str = Path(..., min_length=7, max_length=7, regex=r'X\d{5}0')):
    proj = Project.objects(oid=oid).exclude('id').first()
    if proj:
        register_action('Desconocido', 'OTU', 'Un usuario ha obtenido la OTU {} correctamente'.format(oid), background=background_tasks)
        return proj.otu.to_mongo().to_dict()
    else:
        register_action('Desconocido', 'OTU', 'Un usuario ha intenado obtener la OTU {}, pero no existe'.format(oid), background=background_tasks)
        raise HTTPException(status_code=404, detail='OTU {} not found'.format(oid))
