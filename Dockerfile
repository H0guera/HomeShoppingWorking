FROM python:3.8

COPY requirements.txt /temp/requirements.txt
COPY HomeShopping /HomeShopping
WORKDIR /HomeShopping
EXPOSE 8000

#RUN apk add postgresql-client build-base postgresql-dev

RUN pip install -r /temp/requirements.txt



RUN adduser --disabled-password service-user

USER service-user