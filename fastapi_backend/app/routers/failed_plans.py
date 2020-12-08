from fastapi import APIRouter, Depends,HTTPException, BackgroundTasks
from .google_auth import OAuth2PasswordBearerCookie, oauth2_scheme, get_current_user, User
from fastapi.responses import JSONResponse
from pydantic import EmailStr
from ..models import PlanParseFailedMessage
from ..models import User as UserModel
from .actions_log import register_action

router = APIRouter()
@router.get('/failed-plans', tags=["ProcessingFailed"])
def get_failed_plans(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user),token: str = Depends(oauth2_scheme)):
    user_email = current_user['email']
    user = UserModel.objects(email=user_email).first()
    if user:
        if user.is_admin:
            failed = [x.to_mongo().to_dict() for x in PlanParseFailedMessage.objects.only('id', 'date', 'message').all()]
            result = []
            for fail in failed:
                fail['id'] = str(fail['_id'])
                del fail['_id']
                fail['message'] = fail['message']['message']
                fail['date'] = {
                    '$date': int(fail['date'].timestamp() * 1000) # Why? Who knows
                }
                del fail['plans']
                result.append(fail)
                register_action(user_email, 'FailedPlans', 'El usuario {} ha obtenido los errores en planes'.format(user_email), background=background_tasks)
            return result
        else:
            register_action(user_email, 'FailedPlans', 'El usuario {} ha intenado acceder a los errores en planes sin autorización'.format(user_email), background=background_tasks)
            return JSONResponse(status_code=403, content={'detail': 'Forbidden'})
    else:
        register_action(user_email, 'FailedPlans', 'El usuario {} ha intenado acceder a los errores en planes, pero no existe'.format(user_email), background=background_tasks)
        return JSONResponse(status_code=404, content={'detail': 'User {} not found'.format(user_email)})

@router.get('/failed-plans/{id}', tags=["ProcessingFailed"])
def get_failed_plan_details(background_tasks: BackgroundTasks, id: str, current_user: User = Depends(get_current_user),token: str = Depends(oauth2_scheme)):
    user_email = current_user['email']
    user = UserModel.objects(email=user_email).first()
    if user:
        if user.is_admin:
            failed = PlanParseFailedMessage.objects(id=id).first()
            if failed:
                failed = failed.to_mongo().to_dict()
            else:
                register_action(user_email, 'FailedPlans', 'El usuario {} ha intenado acceder a los detalles de errores en planes {}, pero no existen'.format(user_email, id), background=background_tasks)
                return JSONResponse(status_code=404, content={'detail': 'Failed plans {} not found'.format(id)})
            failed['id'] = str(failed['_id'])
            failed['message'] = failed['message']['message']
            del failed['_id']
            failed['date'] = {
                '$date': int(failed['date'].timestamp() * 1000) # Why? Who knows
            }
            register_action(user_email, 'FailedPlans', 'El usuario {} ha obtenido los detalles de errores en planes {}'.format(user_email, id), background=background_tasks)
            return failed
        else:
            register_action(user_email, 'FailedPlans', 'El usuario {} ha intenado acceder a los errores en planes sin autorización'.format(user_email), background=background_tasks)
            return JSONResponse(status_code=403, content={'detail': 'Forbidden'})
    else:
        register_action(user_email, 'FailedPlans', 'El usuario {} ha intenado acceder a los errores en planes, pero no existe'.format(user_email), background=background_tasks)
        return JSONResponse(status_code=404, content={'detail': 'User {} not found'.format(user_email)})

@router.delete('/failed-plans/{id}', tags=["MissingDocs"])
def delete_failed_plan(background_tasks: BackgroundTasks, id: str, current_user: User = Depends(get_current_user),token: str = Depends(oauth2_scheme)):
    user_email = current_user['email']
    user = UserModel.objects(email=user_email).first()
    if user:
        if user.is_admin:
            failed = PlanParseFailedMessage.objects(id=id).first()
            if failed:
                failed.delete()
            else:
                register_action(user_email, 'FailedPlans', 'El usuario {} ha intenado eliminar los detalles de errores en planes {}, pero no existen'.format(user_email, id), background=background_tasks)
                return JSONResponse(status_code=403, content={'detail': 'Failed plans {} not found'.format(id)})
            register_action(user_email, 'FailedPlans', 'El usuario {} ha eliminado los detalles de errores en planes {}'.format(user_email, id), background=background_tasks)
            return JSONResponse(status_code=200, content={})
        else:
            register_action(user_email, 'FailedPlans', 'El usuario {} ha intenado eliminar los errores en planes sin autorización'.format(user_email), background=background_tasks)
            return JSONResponse(status_code=403, content={'detail': 'Forbidden'})
    else:
        register_action(user_email, 'FailedPlans', 'El usuario {} ha intenado eliminar los errores en planes, pero no existe'.format(user_email), background=background_tasks)
        return JSONResponse(status_code=404, content={'detail': 'User {} not found'.format(user_email)})
