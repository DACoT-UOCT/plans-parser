from pydantic import BaseSettings
from typing import List
from fastapi_mail import FastMail, MessageSchema
from functools import lru_cache
from fastapi.logger import logger
import bson.json_util as bjson
from models import User

class ConnectionConfig(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_PORT: int = 465
    MAIL_SERVER: str
    MAIL_TLS: bool = False
    MAIL_SSL: bool = True
    MAIL_DEBUG: int = 1

class Settings(BaseSettings):
    app_name: str = 'DACoT API'
    mongo_uri: str
    mail_enabled: bool = False
    mail_server: str = ''
    mail_port: int = 0
    mail_pass: str = ''
    mail_user: str = ''
    mail_tls: bool = False
    mail_ssl: bool = False
    mail_config: ConnectionConfig = None
    mail_creation_recipients: List[str] = set()
    docs_samples = dict()

settings = Settings()
logger.info('Started with settings: {}'.format(settings))

if settings.mail_enabled:
    settings.mail_config = ConnectionConfig(
        MAIL_USERNAME = settings.mail_user,
        MAIL_PASSWORD = settings.mail_pass,
        MAIL_PORT = settings.mail_port,
        MAIL_SERVER = settings.mail_server,
        MAIL_TLS = settings.mail_tls,
        MAIL_SSL = settings.mail_ssl,
    )

@lru_cache()
def get_settings():
    return settings

def build_samples_for_docs_from_db():
    user = User.objects(email='admin@dacot.uoct.cl').exclude('id').first()
    if user:
        user_sample = bjson.dumps(user.to_mongo(), sort_keys=True, indent=4)
    else:
        user_sample = None
    docs_samples = {
        'user_model': user_sample
    }
    return docs_samples
