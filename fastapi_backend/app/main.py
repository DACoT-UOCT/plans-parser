from fastapi import Depends, FastAPI, Header, HTTPException, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from mongoengine import connect
from .routers import otu, junctions, users, actions_log, controller_model, commune
from .routers import change_request, external_company, google_auth, failed_plans
from .config import get_settings
from functools import lru_cache
import os
from typing import List
from fastapi.responses import HTMLResponse

app = FastAPI(ocs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

connect(host=get_settings().mongo_uri)

app.include_router(google_auth.router)
app.include_router(users.router)
app.include_router(otu.router)
app.include_router(junctions.router)
app.include_router(change_request.router)
app.include_router(actions_log.router)
app.include_router(commune.router)
app.include_router(controller_model.router)
app.include_router(external_company.router)
app.include_router(failed_plans.router)


@app.post("/files/")
async def create_files(files: List[bytes] = File(...), data: str = Form(...)):
    return {"file_sizes": [len(file) for file in files], "data": data}


@app.post("/uploadfiles/")
async def create_upload_files(files: List[UploadFile] = File(...)):
    return {"filenames": [file.filename for file in files]}
