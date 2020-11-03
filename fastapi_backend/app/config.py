from pydantic import BaseSettings
from fastapi_mail import FastMail, MessageSchema
from functools import lru_cache

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

settings = Settings()

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
