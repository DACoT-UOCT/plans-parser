from fastapi import APIRouter, Body, Query, HTTPException,BackgroundTasks
from flask_mongoengine import MongoEngine
from flask_mongoengine.wtf import model_form
from ..models import models
import json
from mongoengine.errors import ValidationError

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
    background_tasks.add_task(register_action,a_user,context= "POST",component= "Sistema", origin="web")
    mongoUser = models.UOCTUser.from_json(json.dumps(user))
    print(mongoUser)
    try:
        mongoUser.validate()
    except ValidationError as error:
        print(error)
        #raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "There goes my error"},)
        return error
        
    mongoUser.save()
    #mongoUser = mongoUser.reload()
    return {"Respuesta": "Usuario Creado"}

@router.get('/users', tags=["users"])
async def read_users():
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