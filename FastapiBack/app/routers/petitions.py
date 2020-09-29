from fastapi import APIRouter, FastAPI, UploadFile, File,Body, Query, HTTPException,BackgroundTasks, Form
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from pydantic import EmailStr
from pydantic import EmailStr, BaseModel
from typing import List
from ..models import models
from .. import config
from ..config import mail_conf
import json
from functools import lru_cache
from mongoengine.errors import ValidationError

router = APIRouter()

@lru_cache()
def get_settings():
    return config.Settings()



template = """
<html> 
<body>
<p>Hi This test mail using BackgroundTasks
<br>Thanks for using Fastapi-mail</p> 
</body> 
</html>
"""

def register_action(user: str,context: "",component: "", origin: ""):
    #models.history.("dsadsa")
    history = models.History(user=user,context=context,component=component,origin=origin)
    history.save()
    history = history.reload()
    print({"user": user, "context": context, "component": component, "origin": origin })

@router.post("/petitions", tags=["petitions"],status_code=201)
async def create_petition(background_tasks: BackgroundTasks, file: UploadFile= File(...),request: str = Form(...) ):
    a_user= "Camilo"
    email = "darkcamx@gmail.com"
    #background_tasks.add_task(register_action,a_user,context= "POST",component= "Sistema", origin="web")
    mongoRequest = models.Request.from_json(json.dumps(json.loads(request)))
    print(mongoRequest)
    print(email)
    print(file)
    try:
        mongoRequest.validate()
    except ValidationError as error:
        print(error)
        #raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "There goes my error"},)
        return error
    mongoRequest.save()
    mongoUser = mongoRequest.reload()

    message = MessageSchema(
        subject="Fastapi-Mail module",
        receipients=[email],  # List of receipients, as many as you can pass 
        body=template+"ffffffffff",
        subtype="html",
        attachments=[file]
        )

    fm = FastMail(mail_conf)

    background_tasks.add_task(fm.send_message,message)
    background_tasks.add_task(register_action,a_user,context= "POST",component= "Sistema", origin="Create Request")

    

    return [{"username": "Foo"}, {"username": "Bar"}]

@router.put('/accept-petition/{id}', tags=["petition"])
async def accept_petition(background_tasks: BackgroundTasks,id= str):
    a_user= "cponce"
    #modificar estado de peticion de id = id
    #en backgound hacer lo siguiente:
    #necesito recibir empresa para buscar correo en bd
    #recibir archivo y cuerpo , enviar correo con este a empresa correspondiente
    background_tasks.add_task(register_action,a_user,context= "POST",component= "Sistema", origin="Accept Request")
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.put('/reject-petition/{id}', tags=["petition"])
async def accept_petition(background_tasks: BackgroundTasks,id= str):
    a_user= "cponce"
    #modificar estado de peticion de id = id
    #en backgound hacer lo siguiente:
    #necesito recibir empresa para buscar correo en bd
    #recibir archivo y cuerpo , enviar correo con este a empresa correspondiente
    background_tasks.add_task(register_action,a_user,context= "POST",component= "Sistema", origin="Reject Request")
    return [{"username": "Foo"}, {"username": "Bar"}]

