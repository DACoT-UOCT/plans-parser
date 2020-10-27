from fastapi import APIRouter, BackgroundTasks, HTTPException, Form
from ..models import Commune, User,ExternalCompany
from pydantic import EmailStr
from .actions_log import register_action
import json

router = APIRouter()


@router.get('/communes')
async def get_communes(background_tasks: BackgroundTasks):
    r = []
    communes = Commune.objects.all()
    for c in communes:
        r.append({c.name: c.maintainer.name})
    register_action('Desconocido', 'Commune',
                    'Un usuario ha consultado la lista de comunas', background=background_tasks)
    return r
    
@router.put('/edit-commune/{name}', tags=["commune"], status_code=204)
async def edit_commune(background_tasks: BackgroundTasks, user: EmailStr, empresa: EmaiStr,name: str):
    user = User.objects(email=user).first()
    # obtener empresa que me envian
    if user == None:
        raise HTTPException(status_code=404, detail="User not found", headers={"X-Error": "Usuario no encontrado"},)
    if user.is_admin == False:
        raise HTTPException(status_code=403, detail="Forbidden access", headers={"X-Error": "Usuario no encontrado"},)

    empresa = ExternalCompany.objects(email=empresa).first()
    if empresa == None:
        raise HTTPException(status_code=404, detail="Company not found", headers={"X-Error": "Empresa no encontrada"},)
    mongoRequest = Commune.objects(name=name).first()
    if mongoRequest == "":
        raise HTTPException(status_code=404, detail="Item not found", headers={"X-Error": "No Found"},)
    mongoRequest.update(set__maintainer=empresa) 

    background_tasks.add_task(register_action, user, context="Reject Request",
                              action="Actualización de empresa a una comuna", origin="Web")
    return {"message": "Actualizado Correctamente"}
