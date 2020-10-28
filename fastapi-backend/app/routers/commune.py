from fastapi import APIRouter, BackgroundTasks, HTTPException, Form
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
async def edit_commune(background_tasks: BackgroundTasks, user: EmailStr, data: str = Form(...)):
    user = User.objects(email=user).first()
    commune = data.commune
    company_email= data.company_email
    # obtener empresa que me envian
    if user == None:
        raise HTTPException(status_code=404, detail="User not found", headers={"X-Error": "Usuario no encontrado"},)
    if user.is_admin == False:
        raise HTTPException(status_code=403, detail="Forbidden access", headers={"X-Error": "Usuario no encontrado"},)

    company = ExternalCompany.objects(email=company_email).first()
    if company == None:
        raise HTTPException(status_code=404, detail="Company not found", headers={"X-Error": "Empresa no encontrada"},)
    commune_request = Commune.objects(name=commune).first()
    if commune_request == "":
        raise HTTPException(status_code=404, detail="Item not found", headers={"X-Error": "No Found"},)
    commune_request.update(set__maintainer=company) 

    background_tasks.add_task(register_action, user, context="Reject Request",
                              action="Actualización de empresa a una comuna", origin="Web")
    return {"message": "Actualizado Correctamente"}
