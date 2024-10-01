FROM node:current-alpine
RUN mkdir /opt/ui
COPY ui/package.json /opt/ui
COPY ui/package-lock.json /opt/ui
RUN cd /opt/ui && npm install
COPY ui /opt/ui
RUN cd /opt/ui && npm run build

FROM nvidia/cuda:12.6.1-cudnn-runtime-ubuntu24.04

RUN apt update && apt install -y python3 python3-venv python3-pip libgomp1 libogg0 libopus0 opus-tools git && \
    python3 -m venv /opt/env

RUN apt install wget && wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb && \
    dpkg -i cuda-keyring_1.0-1_all.deb  && \
    apt update  && \
    apt install libcudnn8 libcudnn8-dev

COPY requirements/requirements-web.txt /opt/requirements-web.txt
RUN /opt/env/bin/pip install -r /opt/requirements-web.txt

COPY docker/init_models.py /opt/init_models.py
RUN /opt/env/bin/python /opt/init_models.py

COPY --from=0 /opt/ui/build /opt/ui/build

COPY iris /opt/iris
COPY docker /opt/scripts

RUN /opt/env/bin/pip install /opt/iris && mkdir /mount

ENV LD_LIBRARY_PATH=/opt/env/lib64/python3.12/site-packages/nvidia/cublas/lib:/opt/env/lib64/python3.12/site-packages/nvidia/cudnn/lib

ENV IRIS_STATIC_ROOT=/opt/ui/build/
ENV IRIS_SSL_KEYFILE=/mount/certs/key.pem
ENV IRIS_SSL_CERTFILE=/mount/certs/cert.pem
ENV IRIS_DATA_PATH=/mount/data/
ENV HF_HOME=/mount/hf_cache/

CMD bash /opt/scripts/init.sh
