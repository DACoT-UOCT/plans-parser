from fastapi import APIRouter, Body, Query, HTTPException,BackgroundTasks
from flask_mongoengine import MongoEngine
from pydantic import BaseModel
from flask_mongoengine.wtf import model_form
from ..models import models
import json
from mongoengine.errors import ValidationError


router = APIRouter()

def register_action(user: str,context: "",component: "", origin: ""):
    history = models.History(user=user,context=context,component=component,origin=origin)
    history.save()
    history = history.reload()
    print({"user": user, "context": context, "component": component, "origin": origin })

@router.post('/otu',tags=["otu"],status_code=201)
async def create_otu(otu:  dict ,background_tasks: BackgroundTasks):
    a_user= "Camilo"
    background_tasks.add_task(register_action,a_user,context= "POST ",component= "Sistema", origin="Create Request")
    mongoOTU = models.OTU.from_json(json.dumps(otu))
    try:
        mongoOTU.validate()
    except ValidationError as error:
        print(error)
        #raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "There goes my error"},)
        return error
    mongoOTU.save()
    mongoJunction = mongoJunction.reload()
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('/intersections', tags=["intersections"])
async def read_intersections():
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('otu/{id}', tags=["intersections"])
async def read_otu(background_tasks: BackgroundTasks,id: int):
    a_user= "Camilo"
    otu = models.Junction.objects(oid = id)
    if otu == "":
        raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "No Found"},)
        return
    background_tasks.add_task(register_action,a_user,context= "Request OTU",component= "Sistema", origin="web")
    return otu

