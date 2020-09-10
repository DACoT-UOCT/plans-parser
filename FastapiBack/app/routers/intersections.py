from fastapi import APIRouter

router = APIRouter()

@router.post('/intersection',tags=["intersection"])
async def create_intersection():
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('/intersections', tags=["intersections"])
async def read_intersections():
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get('intersections/{id}', tags=["intersections"])
async def read_intersection(id: int):
    return {"id": id}

