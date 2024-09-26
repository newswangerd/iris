FROM node:current-alpine
COPY ui /opt/ui
RUN cd /opt/ui && npm install && npm run build

FROM python:3.12-slim-bookworm

COPY --from=0 /opt/ui/build /opt/ui/build

RUN apt update && apt install -y libgomp1 libogg0 libopus0 opus-tools git

COPY requirements/requirements-web.txt /opt/requirements-web.txt
RUN pip install --upgrade pip && pip install -r /opt/requirements-web.txt

COPY docker/init_models.py /opt/init_models.py
RUN python /opt/init_models.py


COPY . /opt/iris
RUN pip install /opt/iris

ENV IRIS_STATIC_ROOT=/opt/ui/build/
ENV IRIS_SSL_KEYFILE=/etc/iris/certs/key.pem
ENV IRIS_SSL_CERTFILE=/etc/iris/certs/cert.pem

CMD bash /opt/iris/docker/init.sh
