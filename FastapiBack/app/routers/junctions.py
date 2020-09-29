from fastapi import APIRouter, Body, Query, HTTPException,BackgroundTasks
from flask_mongoengine import MongoEngine
from pydantic import BaseModel
from flask_mongoengine.wtf import model_form
from ..models import models
import json
from mongoengine.errors import ValidationError


router = APIRouter()

#class Item(BaseModel):
#    name: str
#    description: Optional[str] = None
#    price: float
#    tax: Optional[float] = None

def register_action(user: str,context: "",component: "", origin: ""):
    #models.history.("dsadsa")
    history = models.History(user=user,context=context,component=component,origin=origin)
    history.save()
    history = history.reload()
    print({"user": user, "context": context, "component": component, "origin": origin })

@router.post('/junctions',tags=["junctions"],status_code=201)
async def create_junction(junction:  dict ,background_tasks: BackgroundTasks):
    a_user= "Camilo"
    background_tasks.add_task(register_action,a_user,context= "POST ",component= "Sistema", origin="Create Request")
    mongoJunction = models.Junction.from_json(json.dumps(junction))
    print(mongoJunction)
    try:
        mongoJunction.validate()
    except ValidationError as error:
        print(error)
        #raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "There goes my error"},)
        return error
    mongoJunction.save()
    mongoJunction = mongoJunction.reload()
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('/junctions', tags=["junctions"])
async def read_junctions(background_tasks: BackgroundTasks):
    a_user= "Camilo"
    background_tasks.add_task(register_action,a_user,context= "GET",component= "Sistema", origin="web")
    #for junction in models.Junction.objects(jid = "J001331"):
        #print(junction.to_json())
    #junctions = junctions.get_or_404();
    return [{"username": "Getting all junctions"}, {"username": "Bar"}]

@router.get('junctions/{id}', tags=["junctions"],status_code=200)
async def read_junction(background_tasks: BackgroundTasks,id: str = Query(... ,min_length=7,max_length=7,regex="")):
    a_user= "Camilo"
    junction = models.Junction.objects(jid = id)
    if junction == "":
        raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "No Found"},)
        return
    background_tasks.add_task(register_action,a_user,context= "GET",component= "Sistema", origin="Consulta Junction")
    junction = models.Junction.objects(jid = id)
    return junction