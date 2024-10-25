FROM alpine

ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 py3-docker-py && ln -sf python3 /usr/bin/python

COPY dogtail.py /

CMD ["python3", "-u", "/dogtail.py"]
