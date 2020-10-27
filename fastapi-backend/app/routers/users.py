from fastapi import APIRouter, Body, Query, HTTPException,BackgroundTasks,Form
from flask_mongoengine import MongoEngine
from pydantic import EmailStr
from flask_mongoengine.wtf import model_form
from ..models import User,ExternalCompany
import json
from .actions_log import register_action
from mongoengine.errors import ValidationError, NotUniqueError

router = APIRouter()

@router.post('/users', tags=["users"],status_code=201)
async def create_user(request: Request ,user: EmailStr,background_tasks: BackgroundTasks):
    user = User.objects(email=user).first()
    if user:
        if user.is_admin:  
            body = await request.json()
            user = User.from_json(json.dumps(body))
            try:
                user.validate()
            except ValidationError as err:
                raise HTTPException(status_code=422, detail=str(err))
            register_action(user, 'Requests', 'El usuario {} ha creado un usuario forma correcta'.format(
                user), background=background_tasks)
            return {}
        else:
            register_action(user, 'Requests', 'El usuario {} ha intenado crear una peticion sin autorizacion'.format(
                user), background=background_tasks)
            raise HTTPException(status_code=403, detail='Forbidden')
    else:
        register_action(user, 'Requests', 'El usuario {} ha intenado crear una peticion, pero no existe'.format(
            user), background=background_tasks)
        raise HTTPException(
            status_code=404, detail='User {} not found'.format(user))
    return {"Respuesta": "Usuario Creado"}


#@router.get("/users/me", tags=["users"])
#async def read_user_me():
 #   return {"username": "fakecurrentuser"}


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

@router.put('/edit-user/{edited_user}', tags=["users"],status_code=204)
async def edit_user(background_tasks: BackgroundTasks,edited_user: str,user: EmailStr ,request: Request):
    user = User.objects(email= user).first()
    edit_user = User.objects(email=edited_user).first()
    if user:
        if user.is_admin:  
            body = await request.json()
            if edit_user:
                company = ExternalCompany.objects(email=body.company)
                if company:
                    #edit_user.update(**body) # si no funciona pasar body a diccionario
                    edit_user.is_admin = body.is_admin
                    edit_user.rol = body.rol
                    edit_user.area = body.area
                    edit_user.company = company
                else:
                    raise HTTPException(
                    status_code=404, detail='Company {} not found'.format(body.company))
            else:
                raise HTTPException(
            status_code=404, detail='User {} not found'.format(edited_user))
            register_action(user, 'Requests', 'El usuario {} ha editado un usuario forma correcta'.format(
                user), background=background_tasks)
            return {}
        else:
            register_action(user, 'Requests', 'El usuario {} ha intenado crear una peticion sin autorizacion'.format(
                user), background=background_tasks)
            raise HTTPException(status_code=403, detail='Forbidden')
    else:
        register_action(user, 'Requests', 'El usuario {} ha intenado crear una peticion, pero no existe'.format(
            user), background=background_tasks)
        raise HTTPException(
            status_code=404, detail='User {} not found'.format(user))
    register_action(user, 'Users', 'El usuario {} ha cambiado los permisos del usuario {}'.format(user,edited_user), background=background_tasks)

@router.delete('/delete-user/{edited_user}',tags=["users"],status_code=204)
async def delete_user(background_tasks: BackgroundTasks,edited_user: str,user: EmailStr ,data: str = Form(...)):
    user = User.objects(email= user).first()
    if user == None:
        raise HTTPException(status_code=404, detail="User not found",headers={"X-Error": "Usuario no encontrado"},)
    if user.is_admin == False:
        raise HTTPException(status_code=403, detail="Forbidden access",headers={"X-Error": "Usuario no encontrado"},)
    edit_user = User.objects(email=edited_user).first()
    if edit_user == None:
        raise HTTPException(status_code=404, detail="User not found",headers={"X-Error": "Usuario no encontrado"},)
    edit_user.delete()
    register_action(user, 'Users', 'El usuario {} ha eliminado al usuario {}'.format(user,edited_user), background=background_tasks)