FROM python:3.8

RUN pip install --upgrade pip

COPY requirements.txt /temp/requirements.txt
RUN pip install -r /temp/requirements.txt
COPY HomeShopping /HomeShopping
WORKDIR /HomeShopping
EXPOSE 8000

RUN adduser --disabled-password service-user

USER service-user