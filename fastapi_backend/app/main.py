from .config import get_settings
from mongoengine import connect

connect(host=get_settings().mongo_uri)

from fastapi import Depends, FastAPI, Header, HTTPException, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from .routers import otu, junctions, users, actions_log, controller_model, commune
from .routers import change_request, external_company, google_auth, failed_plans
from functools import lru_cache
import os
from typing import List
from fastapi.responses import HTMLResponse

openapi_tags_info = [
    {
        'name': 'Junctions',
        'description': 'Intersecciones obtenidas desde el sistema de control de la UOCT. \
            Este endpoint contiene los datos de programación de las intersecciones existentes en la UOCT \
            junto con metadatos georeferenciados de la instalación fisica.'
    },
    {
        'name': 'Commune',
        'description': 'Comunas de la región metropolitana junto con su mantenedor asignado.'
    },
    {
        'name': 'ActionsLog',
        'description': 'Registro de actividades realizadas en la plataforma.'
    },
    {
        'name': 'OTU',
        'description': 'Intersecciones obtenidas desde el sistema de control de la UOCT. \
            En este endpoint estan disponibles las programaciones de las distintas instalaciones semaforicas \
            de la UOCT.'
    },
    {
        'name': 'Users',
        'description': 'Datos sobre los usuarios registrados en la plataforma.'
    },
    {
        'name': 'Security',
        'description': 'Endpoints relacionados al proceso de autenticación en la plataforma.'
    },
    {
        'name': 'MissingDocs',
        'description': 'Endpoints without documentation.'
    }
]

app = FastAPI(openapi_tags=openapi_tags_info)

app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

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


# @app.post("/files/")
# async def create_files(files: List[bytes] = File(...), data: str = Form(...)):
#     return {"file_sizes": [len(file) for file in files], "data": data}
# 
# 
# @app.post("/uploadfiles/")
# async def create_upload_files(files: List[UploadFile] = File(...)):
#     return {"filenames": [file.filename for file in files]}
