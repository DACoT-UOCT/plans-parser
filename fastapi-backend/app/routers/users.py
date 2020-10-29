from fastapi import APIRouter, Body, Query, Request,HTTPException,BackgroundTasks,Form
from flask_mongoengine import MongoEngine
from pydantic import EmailStr
from flask_mongoengine.wtf import model_form
from ..models import User,ExternalCompany
import json
from .actions_log import register_action
from mongoengine.errors import ValidationError, NotUniqueError

router = APIRouter()

@router.post('/users', tags=["users"],status_code=201)
async def create_user(request: Request ,user_email: EmailStr,background_tasks: BackgroundTasks):
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin:  
            body = await request.json()
            new_user = User.from_json(json.dumps(body))
            print(type(body))
            print(body.company)
            company = body["company"]["name"]
            company = ExternalCompany.objects(name=company).first()
            new_user.company = company
            try:
                new_user.validate()
            except ValidationError as err:
                raise HTTPException(status_code=422, detail=str(err))
            new_user = new_user.save()
            register_action(user_email, 'Users', 'El usuario {} ha creado un usuario forma correcta'.format(
                user_email), background=background_tasks)
        else:
            register_action(user_email, 'Users', 'El usuario {} ha intenado crear un usuario sin autorizacion'.format(
                user_email), background=background_tasks)
            raise HTTPException(status_code=403, detail='Forbidden')
    else:
        register_action(user_email, 'Users', 'El usuario {} ha intenado crear un usuario, pero no existe'.format(
            user_email), background=background_tasks)
        raise HTTPException(
            status_code=404, detail='User {} not found'.format(user_email))
    return {"Respuesta": "Usuario Creado"}


#@router.get("/users/me", tags=["users"])
#async def read_user_me():
 #   return {"username": "fakecurrentuser"}


@router.get('/users', tags=["users"],status_code=200)
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

@router.put('/edit-user/{edited_user}', tags=["users"],status_code=200)
async def edit_user(background_tasks: BackgroundTasks,edited_user: str,user_email: EmailStr ,request: Request):
    user = User.objects(email= user_email).first()
    if user:
        if user.is_admin:  
            edit_user = User.objects(email=edited_user).first()
            body = await request.json()
            if edit_user:
                company = ExternalCompany.objects(email=body.company)
                if company:    
                    #edit_user.update(**body) # si no funciona pasar body a diccionario
                    edit_user.is_admin = body.is_admin
                    edit_user.full_name = body.full_name
                    edit_user.rol = body.rol
                    edit_user.area = body.area
                    edit_user.company = company
                    register_action(user_email, 'Users', 'El usuario {} ha editado al usuario {} de forma correcta'.format(user_email,edited_user), background=background_tasks)
                else:
                    edit_user.is_admin = body.is_admin
                    edit_user.full_name = body.full_name
                    edit_user.rol = body.rol
                    edit_user.area = body.area
                    register_action(user_email, 'Users', 'El usuario {} ha editado al usuario {} de forma correcta'.format(user_email,edited_user), background=background_tasks)
            else:
                register_action(user_email, 'Users', 'El usuario {} ha intenado editar un usuario que no existe'.format(
                user_email), background=background_tasks)
                raise HTTPException(
                status_code=404, detail='User {} not found'.format(edited_user))
            return {}
        else:
            register_action(user_email, 'Users', 'El usuario {} ha intenado editar un usuario sin autorizacion'.format(
                user_email), background=background_tasks)
            raise HTTPException(status_code=403, detail='Forbidden')
    else:
        register_action(user_email, 'Users', 'El usuario {} ha intenado editar a un usuario, pero no existe'.format(
            user_email), background=background_tasks)
        raise HTTPException(
            status_code=404, detail='User {} not found'.format(user_email))
    

@router.delete('/delete-user/{edited_user}',tags=["users"],status_code=204)
async def delete_user(background_tasks: BackgroundTasks,edited_user: str,user_email: EmailStr):
    user = User.objects(email= user_email).first()
    if user:
        if user.is_admin:
            edit_user = User.objects(email=edited_user).first()
            if edit_user:
                edit_user.delete()
                register_action(user, 'Users', 'El usuario {} ha eliminado al usuario {} de forma correcta'.format(user_email,edited_user), background=background_tasks)
            else:
                register_action(user_email, 'Users', 'El usuario {} ha intenado eliminar a un usuario que no existe'.format(
                user_email), background=background_tasks)
                raise HTTPException(status_code=404, detail="User {} not found".format(edited_user),headers={"X-Error": "Usuario no encontrado"},)

        else:
            register_action(user_email, 'Users', 'El usuario {} ha intenado eliminar un usuario sin autorizacion'.format(
            user_email), background=background_tasks)
            raise HTTPException(status_code=403, detail="Forbidden access",)
    else:
        register_action(user_email, 'Users', 'El usuario {} ha intenado editar a un usuario, pero no existe'.format(
            user_email), background=background_tasks)
        raise HTTPException(status_code=404, detail="User {} not found".format(user_email),headers={"X-Error": "Usuario no encontrado"},)
        
    
    