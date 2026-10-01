# syntax=docker/dockerfile:1
#Taken from https://docs.docker.com/samples/django/, Cheers!
FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/



