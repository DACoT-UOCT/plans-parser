from fastapi import APIRouter,HTTPException
from ..models import models
import json
from pydantic import EmailStr
from datetime import datetime,timedelta
router = APIRouter()


@router.get('/history', tags=["history"])
async def read_history(user: EmailStr, 
    gte: str=str(datetime.today().year)+"-"+str(datetime.today().month)+"-"+ str(datetime.today().day) ,
    lte: str= str(datetime.today().year)+"-"+str(datetime.today().month)+"-"+ str(datetime.today().day + 1)):
    #print(datetime.now()+ timedelta(1))
    user_f = models.UOCTUser.objects(email=user).first()
    if user_f == None:
        raise HTTPException(status_code=404, detail="User not found",headers={"X-Error": "Usuario no encontrado"},)
        return
    if user_f.is_admin == False:
        raise HTTPException(status_code=403, detail="Forbidden access",headers={"X-Error": "Usuario no encontrado"},)
    actions = []
    for register in models.History.objects(date_modified__gte=gte,date_modified__lte=lte):
        actions.append(json.loads(register.to_json()))
    #print(History[0].date_modified)
    return actions

@router.get('/husers', tags=["husers"])
async def read_husers():
    #for register in models.History.objects():
     #   print(register.date_modified)
    #f = models.
    #print(f[0].to_json())
    return [{"username": "Foo"}, {"username": "Bar"}]


