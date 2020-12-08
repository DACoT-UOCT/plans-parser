from fastapi import APIRouter, Depends,BackgroundTasks
from .google_auth import OAuth2PasswordBearerCookie, oauth2_scheme
from ..models import ControllerModel
from .actions_log import register_action

router = APIRouter()

@router.get('/controller_models', tags=["Controllers"])
async def get_controllers(background_tasks: BackgroundTasks,token: str = Depends(oauth2_scheme)):
    d = {}
    models = ControllerModel.objects.all()
    for m in models:
        if m.company.name not in d:
            d[m.company.name] = {
                'company': m.company.name,
                'models': {}
            }
        fwd = {
            'version': m.firmware_version,
            'checksum': m.checksum,
            'date': {
                '$date': int(m['date'].timestamp() * 1000) # Why? Who knows
            }
        }
        if m.model not in d[m.company.name]['models']:
            d[m.company.name]['models'][m.model] = {
                'name': m.model,
                'firmware': [
                    fwd
                ]
            }
        else:
            d[m.company.name]['models'][m.model]['firmware'].append(fwd)
    r = list(d.values())
    for compd in r:
        compd['models'] = list(compd['models'].values())
    register_action('Desconocido', 'ControllerModels', 'Un usuario ha consultado la lista de modelos de los controladores', background=background_tasks)
    return r
