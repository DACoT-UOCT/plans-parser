import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from .google_auth import OAuth2PasswordBearerCookie, oauth2_scheme
from fastapi.logger import logger
from ..models import User, ActionsLog
from pydantic import EmailStr
from datetime import datetime, timedelta
router = APIRouter()



@router.get('/actions_log', tags=["history"])
async def read_actions(background_tasks: BackgroundTasks,token: str = Depends(oauth2_scheme), user_email: EmailStr, gte: str = str(datetime.today().year)+"-"+str(datetime.today().month)+"-" + str(datetime.today().day), lte: str = str(datetime.today().year)+"-"+str(datetime.today().month)+"-" + str(datetime.today().day + 1)):
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
