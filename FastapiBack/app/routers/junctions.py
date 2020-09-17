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



@router.post('/junctions',tags=["junctions"],status_code=201)
async def create_junction(user:  dict ):
    mongoUser = models.UOCTUser.from_json(json.dumps(user))
    print(mongoUser)
    #try:
    #    mongoUser.validate()
    #except ValidationError as error:
    #    print(error)
        #raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "There goes my error"},)
    #    return error
    #mongoUser.save()
    #mongoUser = mongoUser.reload()
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('/junctions', tags=["junctions"])
async def read_junctions():
    for junction in models.Junction.objects(jid = "J001331"):
        print(junction.to_json())
    #junctions = junctions.get_or_404();
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('junctions/{id}', tags=["junctions"])
async def read_junction(id: str = Query(... ,min_length=7,max_length=7,regex="")):
    junction = models.Junction.objects(jid = id)
    return {"id": id}