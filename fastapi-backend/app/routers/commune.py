from fastapi import APIRouter,BackgroundTasks,HTTPException,Form
from ..models import Commune,History,User
from pydantic import EmailStr
import json

router = APIRouter()

def register_action(user: str,context: "",action: "", origin: ""):
    #models.history.("dsadsa")
    history = History(user=user,context=context,action=action,origin=origin)
    history.save()
    history = history.reload()
    print({"user": user, "context": context, "action": action, "origin": origin })

@router.get('/communes', tags=["commune"],status_code=200)
async def get_communes():
    r = []
    communes = Commune.objects.all()
    for c in communes:
        r.append({c.name: c.maintainer.name})
    return r

@router.put('/edit-commune/{name}', tags=["commune"],status_code=204)
async def edit_commune(background_tasks: BackgroundTasks,user: EmailStr ,name= str,data: str = Form(...)):
    user =User.objects(email=user).first()
    #obtener empresa que me envian
    empresa = "hola"
    if user == None:
        raise HTTPException(status_code=404, detail="User not found",headers={"X-Error": "Usuario no encontrado"},)
        return
    if user.is_admin == False:
        raise HTTPException(status_code=403, detail="Forbidden access",headers={"X-Error": "Usuario no encontrado"},)
    mongoRequest = Commune.objects(name = name)
    get_compaty = empresa
    if mongoRequest == "":
        raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "No Found"},)
        return
    mongoRequest.update(set__maintainer=empresa)#modificar esto

    background_tasks.add_task(register_action,user,context= "Reject Request",action= "Actualización de empresa a una comuna", origin="Web")
    return {"message": "Actualizado Correctamente"}
