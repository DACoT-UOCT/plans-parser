from fastapi import APIRouter
from flask_mongoengine import MongoEngine
from flask_mongoengine.wtf import model_form
from ..models import models

router = APIRouter()

@router.post('/junctions',tags=["junctions"])
async def create_junction():
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('/junctions', tags=["junctions"])
async def read_junctions():
    for junction in models.Junction._Document__objects:
        print(junction.meta)
    #junctions = junctions.get_or_404();
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('junctions/{id}', tags=["junctions"])
async def read_junction(id: int):
    return {"id": id}

