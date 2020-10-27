from fastapi import APIRouter, Body, Query, HTTPException,BackgroundTasks,Form
from flask_mongoengine import MongoEngine
from pydantic import EmailStr
from flask_mongoengine.wtf import model_form
from ..models import models
import json
from mongoengine.errors import ValidationError, NotUniqueError

router = APIRouter()

def register_action(user: str,context: "",component: "", origin: ""):
    #models.history.("dsadsa")
    history = models.History(user=user,context=context,component=component,origin=origin)
    history.save()
    history = history.reload()
    print({"user": user, "context": context, "component": component, "origin": origin })


@router.post("/users", tags=["users"],status_code=201)
async def create_user(user:  dict ,background_tasks: BackgroundTasks):
    a_user= "Camilo"
    mongoUser = models.UOCTUser.from_json(json.dumps(user))
    print(mongoUser)
    try:
        mongoUser.validate()
    except ValidationError as error:
        print(error)
        return error
    
    try:
        mongoUser.save()
    except NotUniqueError:
        raise HTTPException(status_code=409, detail="Duplicated item",headers={"X-Error": "There goes my error"},)
    background_tasks.add_task(register_action,a_user,context= "POST",component= "Sistema", origin="web")
    #mongoUser = mongoUser.reload()
    return {"Respuesta": "Usuario Creado"}

@router.get('/users', tags=["users"])
async def read_users(user: EmailStr):
    user_f = models.UOCTUser.objects(email=user).first()
    if user_f == None:
        raise HTTPException(status_code=404, detail="User not found",headers={"X-Error": "Usuario no encontrado"},)
        return
    print(user_f.is_admin)
    if user_f.is_admin == False:
        raise HTTPException(status_code=403, detail="Forbidden access",headers={"X-Error": "Usuario no encontrado"},)
    users = []
    for user in models.UOCTUser.objects():
        users.append(json.loads(user.to_json()))
    #print(History[0].date_modified)
    return users

@router.get("/users/me", tags=["users"])
async def read_user_me():
    return {"username": "fakecurrentuser"}


@router.get("/users/{username}", tags=["users"])
async def read_user(username: str):
    return {"username": username}

@router.put('/change-permission', tags=["commune"],status_code=204)
async def edit_commune(background_tasks: BackgroundTasks,user: EmailStr ,name= str,data: str = Form(...)):
    user = models.User.objects(email= user).first()
    #como saber si quieren dar o quitar admin
    empresa = "hola"
    if user == None:
        raise HTTPException(status_code=404, detail="User not found",headers={"X-Error": "Usuario no encontrado"},)
        return
    if user.is_admin == False:
        raise HTTPException(status_code=403, detail="Forbidden access",headers={"X-Error": "Usuario no encontrado"},)
    mongoRequest = models.User.objects(email= usuarioobtenido)
    mongoRequest.update(set__isadmin= Depende)