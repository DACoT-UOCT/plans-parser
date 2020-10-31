set -exuo pipefail

docker stop mongodb-run-tests || true
docker rm mongodb-run-tests || true
docker run -d --name mongodb-run-tests -p 27017:27017 docker.io/library/mongo:4.0.19-xenial

coverage run -m unittest -v || true

docker stop mongodb-run-tests
docker rm mongodb-run-tests

coverage report || true
