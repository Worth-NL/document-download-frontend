#!/bin/bash
set -eu

DOCKER_IMAGE_NAME=document-download-frontend
PORT=7001

docker run -it --rm \
  -e NOTIFY_ENVIRONMENT=$NOTIFY_ENVIRONMENT \
  -e FLASK_APP=$FLASK_APP \
  -e FLASK_DEBUG=$FLASK_DEBUG \
  -p ${PORT}:${PORT} \
  -v $(pwd):/home/vcap/app \
  ${DOCKER_IMAGE_NAME} \
  ${@}
