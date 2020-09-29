from tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim-2020-06-06
run python -m pip install --upgrade pip
copy requirements.txt requirements.txt
run python -m pip install -r requirements.txt
copy FastapiBack/app /app
copy run-api.sh /run-api.sh
expose 8080
workdir /
entrypoint /bin/bash /run-api.sh
