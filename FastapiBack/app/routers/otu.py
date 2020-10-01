from fastapi import APIRouter, Body, Query, HTTPException,BackgroundTasks
from flask_mongoengine import MongoEngine
from pydantic import BaseModel, EmailStr
from mongoengine import EmailField
from flask_mongoengine.wtf import model_form
from ..models import models
import json
from mongoengine.errors import ValidationError,NotUniqueError


router = APIRouter()

def register_action(user: str,context: "",component: "", origin: ""):
    history = models.History(user=user,context=context,component=component,origin=origin)
    history.save()
    #history = history.reload()
    print({"user": user, "context": context, "component": component, "origin": origin })

@router.post('/otu',tags=["otu"],status_code=201)
async def create_otu(otu:  dict, user: EmailStr ,background_tasks: BackgroundTasks):
    a_user= "Camilo"
    mongoOTU = models.OTU.from_json(json.dumps(otu))
    print(type(mongoOTU))
    try:
        mongoOTU.validate()
    except ValidationError as error:
        print(error)
        #raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "There goes my error"},)
        return error
    try:
        mongoOTU.save()
    except NotUniqueError:
        #print(error)
        raise HTTPException(status_code=409, detail="Duplicated item",headers={"X-Error": "There goes my error"},)
    background_tasks.add_task(register_action,user,context= "Create OTU request ",component= "Sistema", origin="Web")
    #mongoOTU = mongoOTU.reload()
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('/otu', tags=["otu"])
async def read_users_otu(background_tasks: BackgroundTasks, user: EmailStr):
    a_user= "Camilo"
    user_f = models.UOCTUser.objects(email=user).first()
    if user_f == None:
        raise HTTPException(status_code=404, detail="User not found",headers={"X-Error": "Usuario no encontrado"},)
        return
    otu_list= []
    for otu in models.OTU.objects(metadata__status= "SYSTEM",metadata__status_user= user_f).only('oid', 'metadata.status','metadata.status_user'):
        otu_list.append(json.loads(otu.to_json()))
        #print(otu.metadata.status_user.to_json())
    background_tasks.add_task(register_action,user,context= "Request user OTUs",component= "Sistema", origin="web")
    return otu_list

@router.get('/otu/{id}', tags=["intersections"])
async def read_otu(id: str):
    otudb = models.OTU.objects(oid = id)
    #print(otudb.to_json())
    if not otudb:
        raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "No Found"},)
    otuj = json.loads((otudb[0]).to_json())
    otuj['metadata']['maintainer']= json.loads((otudb[0]).metadata.maintainer.to_json())
    otuj['metadata']['status_user']= json.loads((otudb[0]).metadata.status_user.to_json())
    otuj['metadata']['controller']= json.loads((otudb[0]).metadata.controller.to_json())
    otuj['metadata']['controller']['company']= json.loads((otudb[0]).metadata.controller.company.to_json())

    for idx, junc in enumerate(otudb[0].junctions):
        otuj['junctions'][idx] = json.loads(junc.to_json())   
    #background_tasks.add_task(register_action,a_user,context= "Request OTU",component= "Sistema", origin="web")
    return otuj

