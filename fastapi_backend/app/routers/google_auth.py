from typing import Optional
from datetime import datetime, timedelta
from models import User
import jwt
from jwt import PyJWTError

from fastapi import Depends, FastAPI, HTTPException,APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.security.oauth2 import (
    OAuth2,
    OAuthFlowsModel,
    get_authorization_scheme_param,
)
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, JSONResponse, HTMLResponse
from starlette.requests import Request

from pydantic import BaseModel

import httplib2
from oauth2client import client
from google.oauth2 import id_token
from google.auth.transport import requests

router = APIRouter()

COOKIE_AUTHORIZATION_NAME = "Authorization"
COOKIE_DOMAIN = "dacot.duckdns.org"

PROTOCOL = "http://"
FULL_HOST_NAME = "dacot.duckdns.org"
PORT_NUMBER = 80

CLIENT_ID = "226837255536-1kghlr6q84lc4iroc7dk9ri29v262hs6.apps.googleusercontent.com"
CLIENT_SECRETS_JSON = "client_secret_226837255536-1kghlr6q84lc4iroc7dk9ri29v262hs6.apps.googleusercontent.com.json"

API_LOCATION = f"{PROTOCOL}{FULL_HOST_NAME}:{PORT_NUMBER}"
SWAP_TOKEN_ENDPOINT = "/swap_token"
SUCCESS_ROUTE = "/users/me"
ERROR_ROUTE = "/login_error"

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    "johndoe": {
        "is_admin": False,
        "full_name": "John Doe",
        "email": "myemail@gmail.com",
        "rol": "Empresa",
        "area": "Mantenedora"
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None
    email: str = None


class User(BaseModel):
    is_admin: bool = None
    full_name: str = None
    email: str = None
    rol: str = None
    area: str = None


class OAuth2PasswordBearerCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        header_authorization: str = request.headers.get("Authorization")
        cookie_authorization: str = request.cookies.get("Authorization")

        header_scheme, header_param = get_authorization_scheme_param(
            header_authorization
        )
        cookie_scheme, cookie_param = get_authorization_scheme_param(
            cookie_authorization
        )

        if header_scheme.lower() == "bearer":
            authorization = True
            scheme = header_scheme
            param = header_param

        elif cookie_scheme.lower() == "bearer":
            authorization = True
            scheme = cookie_scheme
            param = cookie_param

        else:
            authorization = False

        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        return param


oauth2_scheme = OAuth2PasswordBearerCookie(tokenUrl="/token")
#app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

def get_user_by_email(email: str):
    users = User.objects().only("email")
    for user in users:
        if user.email == email:
            user_dict = user.to_mongo()
            return User(**user_dict)


def authenticate_user_email(fake_db, email: str):
    user = get_user_by_email(email)
    if not user:
        return False
    return user


def create_access_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except PyJWTError:
        raise credentials_exception
    user = get_user_by_email(fake_users_db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user



@router.post(f"{SWAP_TOKEN_ENDPOINT}", response_model=Token, tags=["security"])
async def swap_token(request: Request = None):
    if not request.headers.get("X-Requested-With"):
        raise HTTPException(status_code=400, detail="Incorrect headers")

    google_client_type = request.headers.get("X-Google-OAuth2-Type")

    if google_client_type == 'server':
        try:
            body_bytes = await request.body()
            auth_code = jsonable_encoder(body_bytes)

            credentials = client.credentials_from_clientsecrets_and_code(
                CLIENT_SECRETS_JSON, ["profile", "email"], auth_code
            )

            http_auth = credentials.authorize(httplib2.Http())

            email = credentials.id_token["email"]

        except:
            raise HTTPException(status_code=400, detail="Unable to validate social login")


    if google_client_type == 'client':
        body_bytes = await request.body()
        auth_code = jsonable_encoder(body_bytes)
        print(auth_code)

        try:
            idinfo = id_token.verify_oauth2_token(auth_code, requests.Request(), CLIENT_ID)

            # Or, if multiple clients access the backend server:
            # idinfo = id_token.verify_oauth2_token(token, requests.Request())
            # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
            #     raise ValueError('Could not verify audience.')

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # If auth request is from a G Suite domain:
            # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
            #     raise ValueError('Wrong hosted domain.')

            if idinfo['email'] and idinfo['email_verified']:
                email = idinfo.get('email')

            else:
                raise HTTPException(status_code=400, detail="Unable to validate social login")

        except:
            raise HTTPException(status_code=400, detail="Unable to validate social login")

    authenticated_user = authenticate_user_email(fake_users_db, email)

    if not authenticated_user:
        raise HTTPException(status_code=400, detail="Incorrect email address")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": authenticated_user.email}, expires_delta=access_token_expires
    )

    token = jsonable_encoder(access_token)

    response = JSONResponse({"access_token": token, "token_type": "bearer"})

    response.set_cookie(
        COOKIE_AUTHORIZATION_NAME,
        value=f"Bearer {token}",
        domain=COOKIE_DOMAIN,
        httponly=True,
        max_age=1800,
        expires=1800,
    )
    return response




@router.get("/")
async def homepage():
    return "Welcome to the security test!"


@router.get(f"{ERROR_ROUTE}", tags=["security"])
async def login_error():
    return "Something went wrong logging in!"


@router.get("/logout", tags=["security"])
async def route_logout_and_remove_cookie():
    response = RedirectResponse(url="/")
    response.delete_cookie(COOKIE_AUTHORIZATION_NAME, domain=COOKIE_DOMAIN)
    return response


@router.get("/secure_endpoint", tags=["security"])
async def get_open_api_endpoint(current_user: User = Depends(get_current_active_user)):
    response = "How cool is this?"
    return response


@router.get("/users/me/", response_model=User, tags=["users"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/users/me/items/", tags=["users"])
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.full_name}]