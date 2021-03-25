FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim-2020-06-06
RUN apt update && apt install -y libmagic1 python3-testresources && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN python -m pip install --no-deps -r requirements.txt
COPY deploy /repo/deploy
COPY tests /repo/tests
COPY run-seed.sh /repo/run-seed.sh
COPY dacot_models /dacot_models
RUN cd /dacot_models && python -m pip install .
COPY fastapi_backend/app /app
COPY run-api.sh /run-api.sh
EXPOSE 8081
WORKDIR /
ENTRYPOINT /bin/bash /run-api.sh
