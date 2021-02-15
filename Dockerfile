FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim-2020-06-06
RUN apt update && apt install -y libmagic1 python3-testresources && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip || true
COPY requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt
COPY fastapi_backend/app /app
COPY models /app/models
COPY run-api.sh /run-api.sh
EXPOSE 8080
WORKDIR /
ENTRYPOINT /bin/bash /run-api.sh
