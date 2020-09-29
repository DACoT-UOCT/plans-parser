from fastapi import APIRouter
from ..models import models
import json
router = APIRouter()


@router.get('/history', tags=["history"])
async def read_history():
    initial_date= "2020-09-20"
    actions = []
    for register in models.History.objects(date_modified__gte=initial_date,date_modified__lte="2020-09-30"):
        actions.append(json.loads(register.to_json()))

    #print(History[0].date_modified)
    return actions

@router.get('/husers', tags=["husers"])
async def read_husers():
    #for register in models.History.objects():
     #   print(register.date_modified)
    #f = models.
    print(f[0].to_json())
    return [{"username": "Foo"}, {"username": "Bar"}]


