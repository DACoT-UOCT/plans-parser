from fastapi import APIRouter
from ..models import ControllerModel

router = APIRouter()

@router.get('/controller_models')
async def get_communes():
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
    return r
