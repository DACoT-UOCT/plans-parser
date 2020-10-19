from fastapi import APIRouter
from ..models import Commune

router = APIRouter()

@router.get('/communes')
async def get_communes():
    r = []
    communes = Commune.objects.all()
    for c in communes:
        r.append({c.name: c.maintainer.name})
    return r
