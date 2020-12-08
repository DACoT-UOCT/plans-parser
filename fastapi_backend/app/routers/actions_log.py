import json
import bson.json_util as bjson
from fastapi import Depends,APIRouter, HTTPException, BackgroundTasks
from .google_auth import OAuth2PasswordBearerCookie, oauth2_scheme
from fastapi.logger import logger
from ..models import User, ActionsLog
from pydantic import EmailStr
from datetime import datetime, timedelta
router = APIRouter()

get_sample = bjson.dumps([ActionsLog.objects().exclude('id').first().to_mongo()], sort_keys=True, indent=4)

@router.get('/actions_log', tags=["ActionsLog"], responses={
    200: {
        "description": "OK. Se ha obtendio el historial de actividades realizadas en la plataforma.",
        "content": {
            "application/json": { "example": get_sample }
        }
    },
    403: {
        "description": "Prohibido. El usuario que realiza esta acción no tiene los permisos suficientes.",
        "content": {
            "application/json": { "example": {"detail": "Forbbiden"} }
        }
    },
    404: {
        "description": "No encontrado. El usuario que esta intentando obtener los registros no existen en la plataforma.",
        "content": {
            "application/json": { "example": {"detail": "User example@google.com not found"} }
        }
    }
})
async def read_actions(background_tasks: BackgroundTasks,user_email: EmailStr,
token: str = Depends(oauth2_scheme),gte: str = str(datetime.today().year)+
"-"+str(datetime.today().month)+"-" + str(datetime.today().day), 
lte: str = str(datetime.today().year)+"-"+str(datetime.today().month)+"-" 
+ str(datetime.today().day + 1)):
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin:
            register_action(user_email, 'ActionLogs', 'El usuario {} ha obtenido los registros entre {} y {} de forma correcta'.format(user_email, gte, lte), background=background_tasks)
            return [x.to_mongo().to_dict() for x in ActionsLog.objects(date__gte=gte, date__lte=lte).exclude('id').all()]
        else:
            register_action(user_email, 'ActionLogs', 'El usuario {} ha intenado acceder a los registros sin autorización'.format(user_email), background=background_tasks)
            raise HTTPException(status_code=403, detail='Forbidden')
    else:
        register_action(user_email, 'ActionLogs', 'El usuario {} ha intenado acceder a los registros, pero no existe'.format(user_email), background=background_tasks)
        raise HTTPException(status_code=404, detail='User {} not found'.format(user_email))

def register_action(user, context, action, background=None):
    def register_action_impl(user, context, action):
        event = ActionsLog(user=user, context=context, action=action, origin='api-backend').save()
        logger.info('log: {}'.format(event.to_json()))
    if background:
        background.add_task(register_action_impl, user, context, action)
    else:
        register_action_impl(user, context, action)
