from fastapi import APIRouter, FastAPI, UploadFile, File,Body, Query, HTTPException,BackgroundTasks, Form
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from fastapi.responses import HTMLResponse
from pydantic import EmailStr, BaseModel
from typing import List
from ..models import models
from .. import config
from ..config import mail_conf
import json
from functools import lru_cache
from mongoengine.errors import ValidationError, NotUniqueError

router = APIRouter()

@lru_cache()
def get_settings():
    return config.Settings()



header= """
<html> 
<body>
<p>Solicitud de nueva instalación
<br></p> 
</body> 
</html>
"""

accept= """
<html> 
<body>
<p>Su solicitud ha sido Aceptada
<br></p> 
</body> 
</html>
"""
reject= """
<html> 
<body>
<p>Su solicitud ha sido Rechazada
<br></p> 
</body> 
</html>
"""

footer= """
<html> 
<body>
<p>Thanks for using Fastapi-mail </p>
</body> 
</html>
"""

def register_action(user: str,context: "",component: "", origin: ""):
    #models.history.("dsadsa")
    history = models.History(user=user,context=context,component=component,origin=origin)
    history.save()
    history = history.reload()
    print({"user": user, "context": context, "component": component, "origin": origin })

@router.post("/request", tags=["requests"],status_code=201)
async def create_petition(background_tasks: BackgroundTasks,user: EmailStr, file: List[UploadFile]= File(default=None),request: str= Form(...) ):
    a_user= "Camilo"
    email = "darkcamx@gmail.com"
    motivo= "Se ha creado una solicitud de instalación, por favor revisar lo más pronto posible"
    #background_tasks.add_task(register_action,a_user,context= "POST",component= "Sistema", origin="web")
    #mongoRequest = models.Request.from_json(json.dumps(json.loads(request)))
    #mongoRequest = models.Request.from_json(json.dumps(request))
    mongoRequest = (json.loads(request))['otu']
    mongoRequest = models.Request.from_json(json.dumps(mongoRequest))
    #print(json.loads(request)['data'])
    #print(type(file))
    print(file)
    try:
        mongoRequest.validate()
    except ValidationError as error:
        return error
    try:
        mongoRequest.save()
    except NotUniqueError:
        raise HTTPException(status_code=409, detail="Duplicated Item",headers={"X-Error": "There goes my error"},)

    #mongoRequest = mongoRequest.reload()
    if file != None:
        message = MessageSchema(
            subject="Fastapi-Mail module",
            receipients=[email],  # List of receipients, as many as you can pass 
            body=header+"Motivo: " + motivo + footer,
            subtype="html",
            attachments=file
            )
    else:
        message = MessageSchema(
            subject="Fastapi-Mail module",
            receipients=[email],  # List of receipients, as many as you can pass 
            body=header+"Motivo: " + motivo + footer,
            subtype="html",
            )
    fm = FastMail(mail_conf)

    background_tasks.add_task(fm.send_message,message)
    background_tasks.add_task(register_action,user,context= "Create Request",component= "Sistema", origin="Web")

    
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.put('/accept-request/{id}', tags=["requests"],status_code=204)
async def accept_petition(background_tasks: BackgroundTasks,user: EmailStr, file: List[UploadFile]= File(default=None),id= str,data: str = Form(...)):
    a_user= "cponce"
    email = json.loads(data)["mails"]
    motivo= "Motivo"
    mongoRequest = models.Request.objects(oid = id)
    if mongoRequest == "":
        raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "No Found"},)
        return
    #Request = json.loads((mongoRequest[0]).to_json())
    mongoRequest.update(set__metadata__status="APPROVED")
    if file != None:
        message = MessageSchema(
            subject="Fastapi-Mail module",
            receipients=email,  # List of receipients, as many as you can pass 
            body=accept+"Motivo: " + motivo + footer,
            subtype="html",
            attachments=file
            )
    else:
        message = MessageSchema(
            subject="Fastapi-Mail module",
            receipients=email,  # List of receipients, as many as you can pass 
            body=accept+"Motivo: " + motivo + footer,
            subtype="html",
            )
    fm = FastMail(mail_conf)

    background_tasks.add_task(fm.send_message,message)
    background_tasks.add_task(register_action,user,context= "Accept Request",component= "Sistema", origin="Web")
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.put('/reject-request/{id}', tags=["requests"],status_code=204)
async def reject_petition(background_tasks: BackgroundTasks,user: EmailStr , file: List[UploadFile]= File(default=None),id= str,data: str = Form(...)):
    a_user= "cponce"
    email = json.loads(data)["mails"]
    motivo= "Motivo"
    mongoRequest = models.Request.objects(oid = id)
    if mongoRequest == "":
        raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "No Found"},)
        return
    #Request = json.loads((mongoRequest[0]).to_json())
    mongoRequest.update(set__metadata__S__status="REJECTED")
    if file != None:
        message = MessageSchema(
            subject="Fastapi-Mail module",
            receipients=email,  # List of receipients, as many as you can pass 
            body=reject+"Motivo: " + motivo + footer,
            subtype="html",
            attachments=file
            )
    else:
        message = MessageSchema(
            subject="Fastapi-Mail module",
            receipients=email,  # List of receipients, as many as you can pass 
            body=reject+"Motivo: " + motivo + footer,
            subtype="html",
            )
    fm = FastMail(mail_conf)

    background_tasks.add_task(fm.send_message,message)
    background_tasks.add_task(register_action,user,context= "Reject Request",component= "Sistema", origin="Web")
    return [{"username": "Foo"}, {"username": "Bar"}]


@router.get('/request', tags=["requests"])
async def read_otu(background_tasks: BackgroundTasks,user: EmailStr):
    a_user= "Camilo" 
    request_list= []
    #filtrar por usuario que consulta
    #ver usuario a cargo
    #requestdb = models.Request.objects(metadata__status='NEW').only('oid')
    #request_conf = models.Request.objects(metadata__status__in=["NEW","UPDATE"]).only('oid', 'metadata.status')
    #if len(request_conf) != 0:
    for request in models.Request.objects(metadata__status__in=["NEW","UPDATE"]).only('oid', 'metadata.status'):
        request_list.append(json.loads(request.to_json()))
    #print(requestdb.to_json()) # NEW , UPDATE
    background_tasks.add_task(register_action,user,context= "Request NEW and UPDATE OTUs",component= "Sistema", origin="web")
    return request_list
