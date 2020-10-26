import json
from fastapi import APIRouter, HTTPException
from ..models import User, ActionsLog
from pydantic import EmailStr
from datetime import datetime, timedelta
router = APIRouter()

@router.get('/actions_log', tags=["history"])
async def read_actions(user_email: EmailStr, gte: str = str(datetime.today().year)+"-"+str(datetime.today().month)+"-" + str(datetime.today().day), lte: str = str(datetime.today().year)+"-"+str(datetime.today().month)+"-" + str(datetime.today().day + 1)):
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin:
            register_action(user_email, 'ActionLogs', 'El usuario {} ha obtenido los registros entre {} y {} de forma correcta'.format(user_email, gte, lte))
            l = [x.to_mongo().to_dict() for x in ActionsLog.objects(date__gte=gte, date__lte=lte).all()]
            for i in l:
                del i['_id']
                i['date'] = str(i['date'])
            return l
        else:
            register_action(user_email, 'ActionLogs', 'El usuario {} ha intenado acceder a los registros sin autorización'.format(user_email))
            raise HTTPException(status_code=403, detail='Forbidden')
    else:
        register_action(user_email, 'ActionLogs', 'El usuario {} ha intenado acceder a los registros, pero no existe'.format(user_email))
        raise HTTPException(status_code=404, detail='User {} not found'.format(user_email))

def register_action(user, context, action):
    event = ActionsLog(user=user, context=context, action=action, origin='api-backend').save()
    print('New log event: {}'.format(event.to_json()))
