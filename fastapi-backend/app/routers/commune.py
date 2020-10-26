from fastapi import APIRouter, BackgroundTasks
from ..models import Commune
from .actions_log import register_action

router = APIRouter()

@router.get('/communes')
async def get_communes(background_tasks: BackgroundTasks):
    r = []
    communes = Commune.objects.all()
    for c in communes:
        r.append({c.name: c.maintainer.name})
    register_action('Desconocido', 'Commune', 'Un usuario ha consultado la lista de comunas', background=background_tasks)
    return r
