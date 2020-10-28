from fastapi import APIRouter, File, Form,BackgroundTasks,UploadFile,HTTPException
from ..models import ExternalCompany,User
from typing import List
from pydantic import EmailStr
from .actions_log import register_action

router = APIRouter()

#@router.put('/edit-company', tags=["external_company"],status_code=204)
#async def reject_petition(background_tasks: BackgroundTasks,user: EmailStr , file: List[UploadFile]= File(default=None),id= str,data: str = Form(...)):
    #a_user= "cponce"
    #email = json.loads(data)["mails"]
    #file= [json.loads(data)["file"]]
    #motivo= "Motivo"
    #motivo= json.loads(data)["comentario"]
    #mongoRequest = models.Request.objects(oid = id)
    #if mongoRequest == "":
        #raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "No Found"},)
        #return
    #Request = json.loads((mongoRequest[0]).to_json())
    #mongoRequest.update(set__metadata__status="REJECTED")
    #if file != None:
        #message = MessageSchema(
            #subject="Fastapi-Mail module",
            #recipients=email,  # List of receipients, as many as you can pass 
            #body=reject+"Motivo: " + motivo + footer,
            #subtype="html",
            #attachments=file
            #)
    #else:
        #message = MessageSchema(
            #subject="Fastapi-Mail module",
            #recipients=email,  # List of receipients, as many as you can pass 
            #body=reject+"Motivo: " + motivo + footer,
            #subtype="html",
            #)
    #fm = FastMail(mail_conf)

    #background_tasks.add_task(fm.send_message,message)
    #background_tasks.add_task(register_action,user,context= "Reject Request",component= "Sistema", origin="Web")
    #return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('/companies', tags=["external_company"],status_code=200)
async def get_companies(background_tasks: BackgroundTasks,user_email: EmailStr ):
    user = User.objects(email=user_email).first()
    if user:
        if user.is_admin:
            result = ExternalCompany.objects.exclude('id').all()
            print("llego aca")
            register_action(user_email, 'Users', 'El usuario {} ha obtenido la lista de usuarios registrados de forma correcta'.format(user_email), background=background_tasks)
            return result
        else:
            register_action(user_email, 'Users', 'El usuario {} ha intenado acceder a la lista de empresas registradas sin autorización'.format(user_email), background=background_tasks)
            raise HTTPException(status_code=403, detail='Forbidden')
    else:
        register_action(user_email, 'Users', 'El usuario {} ha intenado acceder a la lista de empresas registradas, pero no existe'.format(user_email), background=background_tasks)
        raise HTTPException(status_code=404, detail='User {} not found'.format(user_email))



