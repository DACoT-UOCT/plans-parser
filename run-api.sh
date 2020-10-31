mongo_db="$MONGO_DB" mongo_uri="$MONGO_URL" server_email="$FASTAPI_MAIL_USER" email_pass="$FASTAPI_MAIL_PASS" uvicorn --host 0.0.0.0 --port 8080 app.main:app
