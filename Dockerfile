FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim-2020-06-06
RUN apt update && apt install -y libmagic1 python3-testresources patch && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip virtualenv poetry
COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
RUN poetry install
COPY deploy /repo/deploy
COPY tests /repo/tests
COPY run-seed.sh /repo/run-seed.sh
COPY dacot_models /dacot_models
RUN cd /dacot_models && python -m pip install .
COPY fastapi_backend/app /app
COPY run-api.sh /run-api.sh
EXPOSE 8081
WORKDIR /
COPY graphene_arguments.patch /graphene_patch.patch
# RUN patch -p0 --verbose --ignore-whitespace --fuzz 3 < /graphene_patch.patch
ENTRYPOINT /bin/bash /run-api.sh
