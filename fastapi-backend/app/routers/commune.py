from fastapi import APIRouter, BackgroundTasks, HTTPException, Form, Request
from ..models import Commune, User,ExternalCompany
from pydantic import EmailStr
from .actions_log import register_action
import json

router = APIRouter()


@router.get('/communes')
async def get_communes(background_tasks: BackgroundTasks):
    r = []
    communes = Commune.objects().exclude('id').all()
    for c in communes:
        defer = c.to_mongo()
        defer['maintainer'] = c.maintainer.to_mongo()
        del defer['maintainer']['_id']
        r.append(defer.to_dict())
    register_action('Desconocido', 'Commune',
                    'Un usuario ha consultado la lista de comunas', background=background_tasks)
    return r
    
@router.put('/edit-commune', tags=["commune"], status_code=204)
async def edit_commune(background_tasks: BackgroundTasks, user: EmailStr, request: Request):
    user = User.objects(email=user).first()
    if user:
        if user.is_admin:  
            body = await request.json()
            commune = body["commune"]
            company_email = body["company_email"]
            company = ExternalCompany.objects(name=company_email).first()
            print(commune)
            print(company_email)
            if company:
                commune_request = Commune.objects(name=commune).first()
                if commune_request:
                    commune_request.update(set__maintainer=company) 
                    register_action(user, 'Requests', 'El usuario {} ha editado la comuna {} de forma correcta'.format(
                    user,commune), background=background_tasks)
                    return {"message": "Actualizado Correctamente"}
                else:
                    register_action(user, 'Requests', 'El usuario {} ha intenado editar una comuna, pero no existe'.format(
                    user), background=background_tasks)
                    raise HTTPException(
                    status_code=404, detail='Commune {} not found'.format(commune))
            else:
                register_action(user, 'Requests', 'El usuario {} ha intenado editar una comuna, pero la compania no existe'.format(
            user), background=background_tasks)
                raise HTTPException(
                status_code=404, detail='Company {} not found'.format(company_email))
        else:
            register_action(user, 'Requests', 'El usuario {} ha intenado editar una comuna sin autorizacion'.format(
                user), background=background_tasks)
            raise HTTPException(status_code=403, detail='Forbidden')
    else:
        register_action(user, 'Requests', 'El usuario {} ha intenado editar una comuna, pero no existe'.format(
            user), background=background_tasks)
        raise HTTPException(
            status_code=404, detail='User {} not found'.format(user))

    
