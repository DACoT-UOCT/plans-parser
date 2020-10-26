from fastapi import APIRouter, Body, Query, HTTPException,BackgroundTasks
from flask_mongoengine import MongoEngine
from pydantic import EmailStr
from flask_mongoengine.wtf import model_form
from ..models import User
from .actions_log import register_action
from mongoengine.errors import ValidationError, NotUniqueError

router = APIRouter()

# @router.post("/users", tags=["users"],status_code=201)
# async def create_user(user:  dict ,background_tasks: BackgroundTasks):
#     a_user= "Camilo"
#     mongoUser = models.UOCTUser.from_json(json.dumps(user))
#     print(mongoUser)
#     try:
#         mongoUser.validate()
#     except ValidationError as error:
#         print(error)
#         return error
#     
#     try:
#         mongoUser.save()
#     except NotUniqueError:
#         raise HTTPException(status_code=409, detail="Duplicated item",headers={"X-Error": "There goes my error"},)
#     background_tasks.add_task(register_action,a_user,context= "POST",component= "Sistema", origin="web")
#     #mongoUser = mongoUser.reload()
#     return {"Respuesta": "Usuario Creado"}

@router.get('/users', tags=["users"])
async def read_users(user_email: EmailStr, background_tasks: BackgroundTasks):
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin:
            result = []
            for x in User.objects.exclude('id').all():
                if x.rol == 'Empresa':
                    x.select_related()
                    dereference_user = x.to_mongo()
                    dereference_user['company'] = x.company.to_mongo()
                    del dereference_user['company']['_id']
                    result.append(dereference_user.to_dict())
                else:
                    result.append(x.to_mongo().to_dict())
            register_action(user_email, 'Users', 'El usuario {} ha obtenido la lista de usuarios registrados de forma correcta'.format(user_email), background=background_tasks)
            return result
        else:
            register_action(user_email, 'Users', 'El usuario {} ha intenado acceder a la lista de usuarios registrados sin autorización'.format(user_email), background=background_tasks)
            raise HTTPException(status_code=403, detail='Forbidden')
    else:
        register_action(user_email, 'Users', 'El usuario {} ha intenado acceder a la lista de usuarios registrados, pero no existe'.format(user_email), background=background_tasks)
        raise HTTPException(status_code=404, detail='User {} not found'.format(user_email))

# @router.get("/users/me", tags=["users"]) # TODO: SESSION SUPPORT
# async def read_user_me():
#     return {"username": "fakecurrentuser"}
