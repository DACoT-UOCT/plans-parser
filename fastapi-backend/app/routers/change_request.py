from fastapi import APIRouter, Request, FastAPI, UploadFile, File, Body, Query, HTTPException, BackgroundTasks, Form
from typing import Any, Dict
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import EmailStr, BaseModel
from typing import List
from mongoengine.errors import ValidationError
import json
from ..models import User, Project, Comment, OTU
from .actions_log import register_action
from ..config import get_settings
import json
from mongoengine.errors import ValidationError, NotUniqueError

router = APIRouter()

header = '<html><body><p>Solicitud de nueva instalacion<br></p></body></html>'
accept = '<html><body><p>Su solicitud ha sido Aceptada<br></p></body></html>'
reject = '<html><body><p>Su solicitud ha sido Rechazada<br></p></body></html>'
footer = '<html><body><p>Thanks for using fastapi-mail</p></body></html>'

creation_motive = 'Se ha creado una solicitud de instalacion.\nRevisar lo más pronto posible.'

creation_recipients = ['cponce@alumnos.inf.utfsm.cl']


def send_notification_mail(bg, recipients, motive, attachment=None):
    message = MessageSchema(
        subject="fastapi-mail module test",
        recipients=recipients,  # List of receipients, as many as you can pass
        body=header + "Motivo: " + motive + footer,
        subtype="html"
    )
    if attachment:
        message.attachments = attachment
    if get_settings().mail_enabled:
        fm = FastMail(get_settings().mail_config)
        bg.add_task(fm.send_message, message)
        register_action('backend', 'Requests', 'Hemos enviado una notificacion a {}'.format(recipients), background=bg)
    else:
        register_action('backend', 'Requests', 'No hemos enviado ninguna notificacion, debido a que los emails estan desactivados', background=bg)

@router.post("/requests", status_code=201)
async def create_petition(background_tasks: BackgroundTasks, user_email: EmailStr, request: Request):
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin:  # Should be admin?
            body = await request.json()
            p = Project.from_json(json.dumps(body))
            obs_comment = Comment(author=user, message=body['observations'])
            p.observations = [obs_comment]
            p.metadata.img = None
            p.metadata.pdf_data = None
            if p.metadata.status == 'NEW':
                try:
                    p.validate()
                    p = p.save()
                except Exception as err:
                    raise HTTPException(status_code=422, detail=str(err))
                background_tasks.add_task(send_notification_mail, background_tasks, creation_recipients, creation_motive)
                register_action(user_email, 'Requests', 'El usuario {} ha creado la peticion {} de forma correcta'.format(user_email, p.id), background=background_tasks)
                p.delete()
                return JSONResponse(status_code=201, content={'detail': 'Created'})
            else:
                register_action(user_email, 'Requests', 'El usuario {} ha intenado crear una peticion con un estado no valido: {}'.format(user_email, p.metadata.status), background=background_tasks)
                return JSONResponse(status_code=422, content={'detail': 'Invalid status'})
        else:
            register_action(user_email, 'Requests', 'El usuario {} ha intenado crear una peticion sin autorizacion'.format(user_email), background=background_tasks)
        return JSONResponse(status_code=403, content={'detail': 'Forbidden'})
    else:
        register_action(user_email, 'Requests', 'El usuario {} ha intenado crear una peticion, pero no existe'.format(user_email), background=background_tasks)
        return JSONResponse(status_code=404, content={'detail': 'User {} not found'.format(user_email)})

#             y = OTU.objects(oid=body.get('otu', {}).get('oid')).only('id').first()
#             x = Project.objects(metadata__version='base', metadata__status='NEW').only('id').first()
#             print(y)
#             print(x)
#             if y:
#                 y.delete()
#             if x:
#                 x.delete()

#    a_user = "Camilo"
#    email = "darkcamx@gmail.com"
#    motivo = "e"
#    #background_tasks.add_task(register_action,a_user,context= "POST",component= "Sistema", origin="web")
#    #mongoRequest = models.Request.from_json(json.dumps(json.loads(request)))
#    #mongoRequest = models.Request.from_json(json.dumps(request))
#    #mongoRequest = (json.loads(request))['otu']
#    otu_seq = []
#    request_data = json.loads(request)
#    for seq in request_data['secuencias']:
#        otu_seq.extend([json.loads(models.OTUSequenceItem(
#            seqid=seqid).to_json()) for seqid in seq])
#    print(otu_seq)
#    request_data['secuencias'] = otu_seq
#    request_data['metadata']['status_date'] = {
#        "$date": request_data['metadata']['status_date']}
#    request_data['metadata']['installation_date'] = {
#        "$date": request_data['metadata']['installation_date']}
#    mongoRequest = models.Request.from_json(json.dumps(request_data))
#    # print(json.loads(request)['data'])
#    # print(type(file))
#    print(file)
#    try:
#        mongoRequest.validate()
#    except ValidationError as error:
#        return error
#    try:
#        mongoRequest.save()
#    except NotUniqueError:
#        raise HTTPException(status_code=409, detail="Duplicated Item", headers={
#                            "X-Error": "There goes my error"},)
#


# @router.put('/accept-request/{id}', tags=["requests"], status_code=204)
# async def accept_petition(background_tasks: BackgroundTasks, user: EmailStr, file: List[UploadFile] = File(default=None), id=str, data: str = Form(...)):
#     a_user = "cponce"
#     email = json.loads(data)["mails"]
#     #file= [json.loads(data)["file"]]
#     #motivo= "Motivo"
#     motivo = json.loads(data)["comentario"]
#     mongoRequest = models.Request.objects(oid=id)
#     if mongoRequest == "":
#         raise HTTPException(status_code=404, detail="Item not found", headers={
#                             "X-Error": "No Found"},)
#         return
#     #Request = json.loads((mongoRequest[0]).to_json())
#     mongoRequest.update(set__metadata__status="APPROVED")
#     if file != None:
#         message = MessageSchema(
#             subject="Fastapi-Mail module",
#             recipients=email,  # List of receipients, as many as you can pass
#             body=accept+"Motivo: " + motivo + footer,
#             subtype="html",
#             attachments=file
#         )
#     else:
#         message = MessageSchema(
#             subject="Fastapi-Mail module",
#             recipients=email,  # List of receipients, as many as you can pass
#             body=accept+"Motivo: " + motivo + footer,
#             subtype="html",
#         )
#     fm = FastMail(mail_conf)
# 
#     background_tasks.add_task(fm.send_message, message)
#     background_tasks.add_task(
#         register_action, user, context="Accept Request", component="Sistema", origin="Web")
#     return [{"username": "Foo"}, {"username": "Bar"}]
# 
# 
# @router.put('/reject-request/{id}', tags=["requests"], status_code=204)
# async def reject_petition(background_tasks: BackgroundTasks, user: EmailStr, file: List[UploadFile] = File(default=None), id=str, data: str = Form(...)):
#     a_user = "cponce"
#     email = json.loads(data)["mails"]
#     #file= [json.loads(data)["file"]]
#     motivo = "Motivo"
#     motivo = json.loads(data)["comentario"]
#     mongoRequest = models.Request.objects(oid=id)
#     if mongoRequest == "":
#         raise HTTPException(status_code=404, detail="Item not found", headers={
#                             "X-Error": "No Found"},)
#         return
#     #Request = json.loads((mongoRequest[0]).to_json())
#     mongoRequest.update(set__metadata__status="REJECTED")
#     if file != None:
#         message = MessageSchema(
#             subject="Fastapi-Mail module",
#             recipients=email,  # List of receipients, as many as you can pass
#             body=reject+"Motivo: " + motivo + footer,
#             subtype="html",
#             attachments=file
#         )
#     else:
#         message = MessageSchema(
#             subject="Fastapi-Mail module",
#             recipients=email,  # List of receipients, as many as you can pass
#             body=reject+"Motivo: " + motivo + footer,
#             subtype="html",
#         )
#     fm = FastMail(mail_conf)
# 
#     background_tasks.add_task(fm.send_message, message)
#     background_tasks.add_task(
#         register_action, user, context="Reject Request", component="Sistema", origin="Web")
#     return [{"username": "Foo"}, {"username": "Bar"}]
# 
# 
# @router.get('/request', tags=["requests"])
# async def read_otu(background_tasks: BackgroundTasks, user: EmailStr):
#     a_user = "Camilo"
#     request_list = []
#     user_f = models.UOCTUser.objects(email=user).first()
#     if user_f == None:
#         raise HTTPException(status_code=404, detail="User not found", headers={
#                             "X-Error": "Usuario no encontrado"},)
#         return
#     # 'Empresa', 'Personal UOCT
#     print(user_f.rol)
#     if user_f.rol == 'Empresa':
#         for request in models.Request.objects(metadata__status__in=["NEW", "UPDATE", "APPROVED"], metadata__status_user=user).only('oid', 'metadata.status'):
#             request_list.append(json.loads(request.to_json()))
#     else:
#         for request in models.Request.objects(metadata__status__in=["NEW", "UPDATE"]).only('oid', 'metadata.status'):
#             request_list.append(json.loads(request.to_json()))
#     # print(requestdb.to_json()) # NEW , UPDATE
#     background_tasks.add_task(
#         register_action, user, context="Request NEW and UPDATE OTUs", component="Sistema", origin="web")
#     return request_list
# 
# 
# @router.get('/request/{id}', tags=["requests"])
# async def read_otu(background_tasks: BackgroundTasks, id=str):
#     otudb = models.Request.objects(oid=id)
#     # print(otudb.to_json())
#     if not otudb:
#         raise HTTPException(status_code=404, detail="Item not found", headers={
#                             "X-Error": "No Found"},)
#     otuj = json.loads((otudb[0]).to_json())
#     #maintainer = (json.loads((otudb[0]).metadata.to_json()))['maintainer']
#     # print(maintainer)
#     #status_user = json.loads((otudb[0]).metadata.status_user)
#     #controller = json.loads((otudb[0]).metadata.controller)
#     #company = json.loads((otudb[0]).metadata.controller.company)
#     # if otudb[0].metadata.to_mongo()['maintainer'] != '':
#     #otuj['metadata']['maintainer']= json.loads((otudb[0]).metadata.maintainer.to_json())
#     # if otudb[0].metadata.to_mongo()['status_user'] != '':
#     #   otuj['metadata']['status_user']= json.loads((otudb[0]).metadata.status_user.to_json())
#     # if otudb[0].metadata.to_mongo()['controller'] != '':
#     #otuj['metadata']['controller']= json.loads((otudb[0]).metadata.controller.to_json())
#     # if otudb[0].metadata.controller.to_mongo()['controller'] != '':
#     #otuj['metadata']['controller']['company']= json.loads((otudb[0]).metadata.controller.company.to_json())
# 
#     # for idx, junc in enumerate(otudb[0].junctions):
#     #otuj['junctions'][idx] = json.loads(junc.to_json())
# 
#     #background_tasks.add_task(register_action,a_user,context= "Request OTU",component= "Sistema", origin="web")
#     return otuj
# 