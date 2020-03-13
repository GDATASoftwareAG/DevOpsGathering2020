FROM python:3.7.6-alpine3.11

RUN echo "http://dl-8.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories \
     && apk --no-cache --update-cache add postgresql-dev g++ linux-headers gfortran build-base bash libpng-dev openblas-dev wget freetype-dev python3-dev py3-pip \
     && ln -s /usr/include/locale.h /usr/include/xlocale.h \
     && pip3 install setuptools wheel

RUN pip3 install kafka-python==2.0.0
RUN pip3 install numpy
RUN pip3 install jaeger-client
RUN pip3 install prometheus_client
RUN pip3 install elasticsearch
RUN pip3 install neo4jrestclient

COPY . /data/Tracing/

ENV PYTHONPATH=/data/
WORKDIR /data/