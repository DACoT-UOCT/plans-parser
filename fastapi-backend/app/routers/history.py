import json
from fastapi import APIRouter, HTTPException
from ..models import User, ActionsLog
from pydantic import EmailStr
from datetime import datetime, timedelta
router = APIRouter()


@router.get('/history', tags=["history"])
async def read_history(user_email: EmailStr, gte: str = str(datetime.today().year)+"-"+str(datetime.today().month)+"-" + str(datetime.today().day), lte: str = str(datetime.today().year)+"-"+str(datetime.today().month)+"-" + str(datetime.today().day + 1)):
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin:
            return [x for x in ActionsLog.objects(date__gte=gte, date__lte=lte)]
        else:
            raise HTTPException(status_code=403, detail='Forbidden')
    else:
        raise HTTPException(status_code=404, detail='User {} not found'.format(user_email))

