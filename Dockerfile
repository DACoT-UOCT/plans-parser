from python:3.8.4-slim
run python -m pip install --upgrade pip
copy requirements.txt requirements.txt
run python -m pip install -r requirements.txt
copy flask-backend/ .
expose 80
entrypoint flask run --host 0.0.0.0
