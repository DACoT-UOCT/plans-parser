from pydantic import BaseSettings
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = 'DACoT API'
    mongo_uri: str
    mongo_db: str
    mail_enabled: bool = False
    server_email: str = ''
    email_pass: str = ''
    mail_config: ConnectionConfig = None

settings = Settings()

if settings.mail_enabled:
    settings.mail_config = ConnectionConfig(
        MAIL_USERNAME = settings.server_email,
        MAIL_PASSWORD = settings.email_pass,
        MAIL_PORT = 587,
        MAIL_SERVER = "smtp.gmail.com",
        MAIL_TLS = True,
        MAIL_SSL = False
    )

@lru_cache()
def get_settings():
    return settings
