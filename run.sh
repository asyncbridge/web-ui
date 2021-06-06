#!/bin/bash
docker run -p 80:5000 -d --env REDIS_HOST='localhost' --env REDIS_PORT=6347 --env REDIS_DB=0 aibakevision/web-ui:0.0.1
