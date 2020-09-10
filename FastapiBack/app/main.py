from fastapi import Depends, FastAPI, Header, HTTPException
from mongoengine import connect
from .routers import intersections, junctions

app = FastAPI()


async def get_token_header(x_token: str = Header(...)):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


#app.include_router(users.router)
app.include_router(intersections.router)
app.include_router(junctions.router)
#app.include_router(
  #  items.router,
   # prefix="/items",
    #tags=["items"],
    #dependencies=[Depends(get_token_header)],
    #responses={404: {"description": "Not found"}},
#)