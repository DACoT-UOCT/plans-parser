from fastapi import APIRouter, File, Form,BackgroundTasks,UploadFile
from ..models import ExternalCompany
from typing import List
from pydantic import EmailStr

router = APIRouter()

@router.put('/edit-company', tags=["external_company"],status_code=204)
async def reject_petition(background_tasks: BackgroundTasks,user: EmailStr , file: List[UploadFile]= File(default=None),id= str,data: str = Form(...)):
    a_user= "cponce"
    email = json.loads(data)["mails"]
    #file= [json.loads(data)["file"]]
    motivo= "Motivo"
    motivo= json.loads(data)["comentario"]
    mongoRequest = models.Request.objects(oid = id)
    if mongoRequest == "":
        raise HTTPException(status_code=404, detail="Item not found",headers={"X-Error": "No Found"},)
        return
    #Request = json.loads((mongoRequest[0]).to_json())
    mongoRequest.update(set__metadata__status="REJECTED")
    if file != None:
        message = MessageSchema(
            subject="Fastapi-Mail module",
            recipients=email,  # List of receipients, as many as you can pass 
            body=reject+"Motivo: " + motivo + footer,
            subtype="html",
            attachments=file
            )
    else:
        message = MessageSchema(
            subject="Fastapi-Mail module",
            recipients=email,  # List of receipients, as many as you can pass 
            body=reject+"Motivo: " + motivo + footer,
            subtype="html",
            )
    fm = FastMail(mail_conf)

    background_tasks.add_task(fm.send_message,message)
    background_tasks.add_task(register_action,user,context= "Reject Request",component= "Sistema", origin="Web")
    return [{"username": "Foo"}, {"username": "Bar"}]

