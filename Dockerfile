FROM alpine

RUN apk add --update --no-cache python3 py3-docker-py && ln -sf python3 /usr/bin/python

COPY docker_logger.py /

CMD ["python3", "-u", "/docker_logger.py"]
