from fastapi import APIRouter, Body
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

@router.post('/junctions',tags=["junctions"])
async def create_junction(user:  dict ):
    mongoUser = models.UOCTUser.from_json(json.dumps(user))
    try:
        mongoUser.validate()
    except ValidationError as error:
        print(error)
        return error
    mongoUser.save()
    mongoUser = mongoUser.reload()
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('/junctions', tags=["junctions"])
async def read_junctions():
    for junction in models.Junction.objects(jid = "J001331"):
        print(junction.to_json())
    #junctions = junctions.get_or_404();
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('junctions/{id}', tags=["junctions"])
async def read_junction(id: int):
    return {"id": id}

