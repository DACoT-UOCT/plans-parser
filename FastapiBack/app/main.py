from fastapi import Depends, FastAPI, Header, HTTPException
from mongoengine import connect
from .routers import otu, junctions,history,users,petitions
from . import config
from functools import lru_cache
import os


app = FastAPI()


@lru_cache()
def get_settings():
    return config.Settings()

#connect('dacot-dev', host='mongodb://54.224.251.49:30001,54.224.251.49:30002,54.224.251.49:30003/?replicaset=rsuoct')
#connect(host='mongodb://127.0.0.1:27017/UOCT')
connect(host= get_settings().mongo_uri)
#async def get_token_header(x_token: str = Header(...)):
 #   if x_token != "fake-super-secret-token":
  #      raise HTTPException(status_code=400, detail="X-Token header invalid")


app.include_router(users.router)
app.include_router(otu.router)
app.include_router(junctions.router)
app.include_router(petitions.router)
app.include_router(history.router)
#app.include_router(
  #  items.router,
   # prefix="/items",
    #tags=["items"],
    #dependencies=[Depends(get_token_header)],
    #responses={404: {"description": "Not found"}},
#)