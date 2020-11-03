from tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim-2020-06-06
run apt update && apt install -y libmagic1 && rm -rf /var/lib/apt/lists/*
run python -m pip install --upgrade pip
copy requirements.txt requirements.txt
run python -m pip install -r requirements.txt
copy fastapi_backend/app /app
copy models /app/models
copy run-api.sh /run-api.sh
expose 8080
workdir /
entrypoint /bin/bash /run-api.sh
