from fastapi import APIRouter, Request, FastAPI, UploadFile, File, Body, Query, HTTPException, BackgroundTasks, Form, Path
from typing import Any, Dict
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import EmailStr, BaseModel
from typing import List
from mongoengine.errors import ValidationError
import json
from ..models import User, Project, Comment, OTU, FileField, Commune, Junction, DACoTBackendException
from ..models import ControllerModel, ExternalCompany
from .actions_log import register_action
from ..config import get_settings
from mongoengine.errors import ValidationError, NotUniqueError
from pymongo.errors import DuplicateKeyError
import base64
import magic
import datetime

router = APIRouter()

header = '<html><body><p>Solicitud de nueva instalacion<br></p></body></html>'
footer = '<html><body><p>Thanks for using fastapi-mail</p></body></html>'

UPDATE_MOTIVE_MESSAGES = {
    'ACCEPTED': '<html><body><p>Su solicitud ha sido Aceptada<br></p></body></html>',
    'REJECTED': '<html><body><p>Su solicitud ha sido Rechazada<br></p></body></html>'
}

creation_motive = 'Se ha creado una solicitud de instalacion.\nRevisar lo más pronto posible.'

creation_recipients = ['cponce@alumnos.inf.utfsm.cl']

STATUS_CREATE_OK = 'El usuario {} ha creado la peticion {} de forma correcta'
STATUS_CREATE_FORBIDDEN = 'El usuario {} ha intenado crear una peticion sin autorizacion'
STATUS_CREATE_ERROR = 'El usuario {} no ha logrado crear una peticion: {}'
STATUS_USER_NOT_FOUND = 'El usuario {} no existe'

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

def __base64file_to_bytes(base64data):
    _, filedata = base64data.split(',')
    try:
        b64bytes = base64.b64decode(filedata)
    except Exception as excep:
        return False, str(excep)
    mime = magic.from_buffer(b64bytes[0:2048], mime=True)
    if mime in ['image/jpeg', 'image/png', 'application/pdf']:
        return b64bytes, mime
    else:
        return False, 'Invalid content-type of file data: {}'.format(mime)

def __build_otu_from_dict(otu_dict):
    junc_objs = []
    for junc in otu_dict['junctions']:
        new_obj = Junction.from_json(json.dumps(junc))
        new_obj.metadata.sales_id = round((int(junc['jid'][1:]) * 11) / 13.0)
        new_obj.metadata.location = (0, 0) # FIXME: Get this value from frontend
        new_obj.validate()
        junc_objs.append(new_obj)
    del otu_dict['junctions']
    otu_obj = OTU.from_json(json.dumps(otu_dict))
    otu_obj.junctions = junc_objs
    return otu_obj

def __build_new_project(req_dict, user, bgtask):
    try:
        p = Project.from_json(json.dumps(req_dict))
    except Exception as err:
        raise DACoTBackendException(status_code=422, details='Invalid JSON data for Project model: {}'.format(err))
    p.metadata.status_date = datetime.datetime.now()
    p.metadata.status_user = user
    if user.rol == 'Empresa':
        p.metadata.installation_company = user.company
    p.metadata.maintainer = ExternalCompany.objects(name=req_dict['metadata']['maintainer']).first()
    if not p.metadata.maintainer:
        raise DACoTBackendException(status_code=422, details='ExternalCompany not found: {}'.format(req_dict['metadata']['maintainer']))
    #; p.metadata.commune = Commune.objects(name=p['metadata']['commune'].upper()).first() # FIXME: ValidationError (Project:None) (commune.StringField only accepts string values: ['metadata'])
    obs_comment = Comment(author=user, message=req_dict['observations'])
    p.observations = [obs_comment]
    p.metadata.img = None
    p.metadata.pdf_data = None
    file_bytes_img, type_or_err_img = __base64file_to_bytes(req_dict['metadata']['img'])
    if not file_bytes_img:
        register_action(user.email, 'Requests', STATUS_CREATE_ERROR.format(user.email, type_or_err_img), background=bgtask)
        raise DACoTBackendException(status_code=422, details='Img: {}'.format(str(type_or_err_img)))
    file_bytes_pdf, type_or_err_pdf = __base64file_to_bytes(req_dict['metadata']['pdf_data'])
    if not file_bytes_pdf:
        register_action(user.email, 'Requests', STATUS_CREATE_ERROR.format(user.email, type_or_err_pdf), background=bgtask)
        raise DACoTBackendException(status_code=422, details='PDF: {}'.format(str(type_or_err_pdf)))
    p.otu = __build_otu_from_dict(req_dict['otu'])
    ctrl_model_dict = req_dict['controller']['model']
    p.controller.model = ControllerModel.objects(
        company=ExternalCompany.objects(name=ctrl_model_dict['company']['name']).first(),
        model=ctrl_model_dict['model'],
        firmware_version=ctrl_model_dict['firmware_version'],
        checksum=ctrl_model_dict['checksum']
    ).first()
    if not p.controller.model:
        raise DACoTBackendException(status_code=422, details='Controller model not found: {}'.format(ctrl_model_dict))
    return p, {'img': (file_bytes_img, type_or_err_img), 'pdf': (file_bytes_pdf, type_or_err_pdf)}

@router.post("/requests", status_code=201)
async def create_request(bgtask: BackgroundTasks, user_email: EmailStr, request: Request):
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin or user.rol == 'Empresa':
            try:
                body = await request.json()
            except json.decoder.JSONDecodeError as err:
                return JSONResponse(status_code=422, content={'detail': 'Invalid JSON document: {}'.format(err)})
            if body['metadata']['status'] == 'NEW':
                try:
                    new_project, files = __build_new_project(body, user, bgtask)
                    new_project = new_project.save_with_transaction()
                    # TODO: Optimization = Search for md5 instead of re-inserting file
                    new_project.metadata.img.put(files['img'][0], content_type=files['img'][1])
                    new_project.metadata.pdf_data.put(files['pdf'][0], content_type=files['pdf'][1])
                    new_project.save()
                except DACoTBackendException as err:
                    register_action(user.email, 'Requests', STATUS_CREATE_ERROR.format(user.email, err), background=bgtask)
                    return JSONResponse(status_code=err.get_status(), content={'detail': err.get_details()})
                else:
                    register_action(user.email, 'Requests', STATUS_CREATE_OK.format(user.email, new_project.id), background=bgtask)
                    background_tasks.add_task(send_notification_mail, background_tasks, creation_recipients, creation_motive)
                    return JSONResponse(status_code=201, content={'detail': 'Created'})
        else:
            register_action(user_email, 'Requests', STATUS_CREATE_FORBIDDEN.format(user_email), background=bgtask)
            return JSONResponse(status_code=403, content={'detail': 'Forbidden'})
    else:
        register_action(user_email, 'Requests', STATUS_USER_NOT_FOUND.format(user_email), background=bgtask)
        return JSONResponse(status_code=404, content={'detail': 'User {} not found'.format(user_email)})

@router.get('/requests')
async def get_requests(bgtask: BackgroundTasks, user_email: EmailStr):
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin or user.rol == 'Personal UOCT' or user.rol == 'Empresa':
            if user.rol == 'Empresa':
                requests_by_maintainer = Project.objects(metadata__status__in=['NEW', 'UPDATE', 'APPROVED', 'REJECTED'], metadata__maintainer=user.company).only('oid', 'metadata.status').exclude('id')
                requests_by_installation_user = Project.objects(metadata__status__in=['NEW', 'UPDATE', 'APPROVED', 'REJECTED'], metadata__installation_company=user.company).only('oid', 'metadata.status').exclude('id')
                requests = dict()
                for req in list(requests_by_maintainer) + list(requests_by_installation_user):
                    requests[req.oid] = req
                requests = requests.values()
            else:
                requests = Project.objects().only('oid', 'metadata.status').exclude('id') # TODO: Check this
            requests = [r.to_mongo().to_dict() for r in requests]
            # BUG: mongoengine returns default fields when using `only`. See https://github.com/MongoEngine/mongoengine/issues/2030
            for r in requests:
                r.pop('headers')
                r.pop('observations') # FIXME: Is this ok? check with frontend.
                r['metadata'].pop('status_date')
                r['metadata'].pop('region')
            return JSONResponse(status_code=200, content=requests)
        else:
            register_action(user_email, 'Requests', STATUS_CREATE_FORBIDDEN.format(user_email), background=bgtask)
            return JSONResponse(status_code=403, content={'detail': 'Forbidden'})
    else:
        register_action(user_email, 'Requests', STATUS_USER_NOT_FOUND.format(user_email), background=bgtask)
        return JSONResponse(status_code=404, content={'detail': 'User {} not found'.format(user_email)})

@router.get('/requests/{oid}')
async def get_single_requests(bgtask: BackgroundTasks, user_email: EmailStr, oid: str = Path(..., min_length=7, max_length=7, regex=r'X\d{5}0')):
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin or user.rol == 'Personal UOCT' or user.rol == 'Empresa':
            request = Project.objects(metadata__status__in=['NEW', 'UPDATE', 'APPROVED', 'REJECTED'], oid=oid).exclude('id', 'metadata.pdf_data').first()
            if not request:
                return JSONResponse(status_code=404, content={'detail': 'Request {} not found'.format(oid)})
            request.select_related()
            defer = request.to_mongo()
            defer['metadata']['status_user'] = request.metadata.status_user.to_mongo()
            del defer['metadata']['status_user']['_id']
            if 'company' in defer['metadata']['status_user']:
                defer['metadata']['status_user']['company'] = request.metadata.status_user.company.to_mongo()
                del defer['metadata']['status_user']['company']['_id']
            defer['metadata']['maintainer'] = request.metadata.maintainer.to_mongo()
            del defer['metadata']['maintainer']['_id']
            defer['otu'] = request.otu.to_mongo()
            del defer['otu']['_id']
            defer['controller']['model'] = request.controller.model.to_mongo()
            del defer['controller']['model']['_id']
            if 'company' in defer['controller']['model']:
                defer['controller']['model']['company'] = request.controller.model.company.to_mongo()
                del defer['controller']['model']['company']['_id']
            for idx, obs in enumerate(defer['observations']):
                obs['author'] = request.observations[idx].author.to_mongo()
                if 'company' in obs['author']:
                    obs['author']['company'] = request.observations[idx].author.company.to_mongo()
                    del obs['author']['company']['_id']
                del obs['author']['_id']
            for idx, _ in enumerate(defer['otu']['junctions']):
                defer['otu']['junctions'][idx] = request.otu.junctions[idx].to_mongo()
                del defer['otu']['junctions'][idx]['_id']
            # Why? Who knows
            defer['metadata']['status_date'] = {
                '$date': int(defer['metadata']['status_date'].timestamp() * 1000)
            }
            defer['metadata']['installation_date'] = {
                '$date': int(defer['metadata']['installation_date'].timestamp() * 1000)
            }
            defer['observations'] = defer['observations'][-1]['message']
            defer['metadata']['img'] = 'data:{};base64,{}'.format(request.metadata.img.content_type, base64.b64encode(request.metadata.img.read()).decode('utf-8'))
            if 'installation_company' in defer['metadata']:
                defer['metadata']['installation_company'] = request.metadata.installation_company.to_mongo()
                del defer['metadata']['installation_company']['_id']
            return defer.to_dict()
        else:
            register_action(user_email, 'Requests', STATUS_CREATE_FORBIDDEN.format(user_email), background=bgtask)
            return JSONResponse(status_code=403, content={'detail': 'Forbidden'})
    else:
        register_action(user_email, 'Requests', STATUS_USER_NOT_FOUND.format(user_email), background=bgtask)
        return JSONResponse(status_code=404, content={'detail': 'User {} not found'.format(user_email)})

async def __process_accept_or_reject(oid, new_status, user_email, request, bgtask):
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin or user.rol == 'Personal UOCT':
            try:
                body = await request.json()
            except json.decoder.JSONDecodeError as err:
                return JSONResponse(status_code=422, content={'detail': 'Invalid JSON document: {}'.format(err)})
            request = Project.objects(metadata__status__in=['NEW', 'UPDATE'], oid=oid).exclude('metadata.pdf_data').first()
            if not request:
                return JSONResponse(status_code=404, content={'detail': 'Request {} not found'.format(oid)})
            # request.metadata.status = new_status #FIXME: Apply this
            request.observations.append(Comment(author=user, message=body['comentario']))
            request.save()
            # TODO: send bae64file as attachment
            bgtask.add_task(send_notification_mail, bgtask, body['mails'], UPDATE_MOTIVE_MESSAGES[new_status])
            return JSONResponse(status_code=200, content={})
        else:
            register_action(user_email, 'Requests', STATUS_CREATE_FORBIDDEN.format(user_email), background=bgtask)
            return JSONResponse(status_code=403, content={'detail': 'Forbidden'})
    else:
        register_action(user_email, 'Requests', STATUS_USER_NOT_FOUND.format(user_email), background=bgtask)
        return JSONResponse(status_code=404, content={'detail': 'User {} not found'.format(user_email)})

@router.put('/requests/{oid}/accept')
async def accept_request(bgtask: BackgroundTasks, user_email: EmailStr, request: Request, oid: str = Path(..., min_length=7, max_length=7, regex=r'X\d{5}0')):
    return await __process_accept_or_reject(oid, 'ACCEPTED', user_email, request, bgtask)

@router.put('/requests/{oid}/reject')
async def reject_request(bgtask: BackgroundTasks, user_email: EmailStr, request: Request, oid: str = Path(..., min_length=7, max_length=7, regex=r'X\d{5}0')):
    return await __process_accept_or_reject(oid, 'REJECTED', user_email, request, bgtask)

@router.put('/requests/{oid}/pdf')
async def get_pdf_data(bgtask: BackgroundTasks, user_email: EmailStr, oid: str = Path(..., min_length=7, max_length=7, regex=r'X\d{5}0')):
    return JSONResponse(status_code=200, content={})

@router.put('/requests/{oid}/delete')
async def delete_request(bgtask: BackgroundTasks, user_email: EmailStr, oid: str = Path(..., min_length=7, max_length=7, regex=r'X\d{5}0')):
    return JSONResponse(status_code=200, content={})
