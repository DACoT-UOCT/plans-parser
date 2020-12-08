from fastapi import APIRouter, Depends,BackgroundTasks, HTTPException, Form, Request
from .google_auth import OAuth2PasswordBearerCookie, oauth2_scheme, get_current_user, User
from ..models import Commune, User,ExternalCompany
from pydantic import EmailStr
from .actions_log import register_action
import bson.json_util as bjson
import json

router = APIRouter()

sample = Commune.objects().exclude('id').first().to_mongo()
sample['maintainer'] = Commune.objects().exclude('id').first().maintainer.to_mongo()
del sample['maintainer']['_id']

get_sample = bjson.dumps([sample], sort_keys=True, indent=4)

@router.get('/communes', status_code=200, tags=["Commune"], responses={
    200: {
        "description": "OK. Se ha obtenido la lista de comunas de forma correcta.",
        "content": {
            "application/json": { "example": get_sample }
        }
    }
})
async def get_communes(background_tasks: BackgroundTasks):
    r = []
    communes = Commune.objects().exclude('id').all()
    for c in communes:
        defer = c.to_mongo()
        if 'maintainer' in defer:
            defer['maintainer'] = c.maintainer.to_mongo()
            del defer['maintainer']['_id']
        r.append(defer.to_dict())
    register_action('Desconocido', 'Commune', 'Un usuario ha consultado la lista de comunas', background=background_tasks)
    return r

@router.put('/edit-commune', tags=["MissingDocs"], status_code=200)
async def edit_commune(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), request: Request,token: str = Depends(oauth2_scheme)):
    user_email = current_user['email']
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin:  
            body = await request.json()
            commune = body["commune"]
            company_email = body["company_email"]
            commune_request = Commune.objects(name=commune).first()
            if commune_request:
                company = ExternalCompany.objects(name=company_email).first()
                if company:
                    commune_request.update(set__maintainer=company) 
                    register_action(user_email, 'Communes', 'El usuario {} ha editado la comuna {} de forma correcta'.format(
                    user_email,commune), background=background_tasks)
                    return {"message": "Actualizado Correctamente"}
                else:
                    commune_request.update(unset__maintainer="") 
                    #register_action(user_email, 'Communes', 'El usuario {} ha intenado editar una comuna, pero la compania no existe'.format(
                    #user_email), background=background_tasks)
                    register_action(user_email, 'Communes', 'El usuario {} ha editado la comuna {} de forma correcta'.format(
                    user_email,commune), background=background_tasks)
                    return {"message": "Actualizado Correctamente"}
                    #raise HTTPException(
                    #status_code=404, detail='Company {} not found'.format(company_email))
            else:
                register_action(user_email, 'Communes', 'El usuario {} ha intenado editar una comuna, pero no existe'.format(
                user_email), background=background_tasks)
                raise HTTPException(
                status_code=404, detail='Commune {} not found'.format(commune))
        else:
            register_action(user_email, 'Communes', 'El usuario {} ha intenado editar una comuna sin autorizacion'.format(
                user_email), background=background_tasks)
            raise HTTPException(status_code=403, detail='Forbidden')
    else:
        register_action(user_email, 'Communes', 'El usuario {} ha intenado editar una comuna, pero no existe'.format(
            user_email), background=background_tasks)
        raise HTTPException(
            status_code=404, detail='User {} not found'.format(user))

    
