from pydantic import BaseSettings
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig

class Settings(BaseSettings):
    app_name: str = "Awesome API"
    mongo_uri: str
    server_email: str
    email_pass: str


settings = Settings(_env_file='.env', _env_file_encoding='utf-8')

mail_conf = ConnectionConfig(
    MAIL_USERNAME = settings.server_email,
    MAIL_PASSWORD = settings.email_pass,
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_TLS = True,
    MAIL_SSL = False
)