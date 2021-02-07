from .config import get_settings
from mongoengine import connect
from starlette.graphql import GraphQLApp
from .graphql_schema import dacot_schema
from fastapi import FastAPI, Request
from starlette.datastructures import URL

connect(host=get_settings().mongo_uri)

api_description = '''
API del proyecto Datos Abiertos para el Control de Tránsito
(DACoT) desarrollado por SpeeDevs en colaboración con la Unidad Operativa de
Control de Tránsito (UOCT) de la región Metropolitana en el contexto de la
XXVIII Feria de Software del Departamento de Informática en la Universidad
Técnica Federico Santa María.
'''

app = FastAPI(
    title='DACoT API',
    version='v0.2',
    description=api_description
)

graphql_app = GraphQLApp(schema=dacot_schema)

@app.get('/')
async def graphiql(request: Request):
    request._url = URL('/graphql')
    return await graphql_app.handle_graphiql(request=request)

@app.post('/graphql')
async def graphql(request: Request):
    return await graphql_app.handle_graphql(request=request)
