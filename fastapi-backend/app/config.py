from pydantic import BaseSettings
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

class Settings(BaseSettings):
    app_name: str = 'DACoT API'
    mongo_uri: str
    mongo_db: str
    mail_enabled: bool = False
    server_email: str = ''
    email_pass: str = ''

settings = Settings()

if settings.mail_enabled:
    mail_conf = ConnectionConfig(
        MAIL_USERNAME = settings.server_email,
        MAIL_PASSWORD = settings.email_pass,
        MAIL_PORT = 587,
        MAIL_SERVER = "smtp.gmail.com",
        MAIL_TLS = True,
        MAIL_SSL = False
    )
