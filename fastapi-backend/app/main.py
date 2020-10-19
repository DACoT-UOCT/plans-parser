from fastapi import Depends, FastAPI, Header, HTTPException,Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from mongoengine import connect
from .routers import otu, junctions,history,users,petitions
from . import config
from functools import lru_cache
import os
from typing import List
from fastapi.responses import HTMLResponse



app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

#======================================================================
@app.post("/files/")
async def create_files(files: List[bytes] = File(...),data: str= Form(...)):
    return {"file_sizes": [len(file) for file in files],"data":data}


@app.post("/uploadfiles/")
async def create_upload_files(files: List[UploadFile] = File(...)):
    return {"filenames": [file.filename for file in files]}


@app.get("/")
async def main():
    content = """
<body>
<H5> DACoT 
</body>
    """
    return HTMLResponse(content=content)