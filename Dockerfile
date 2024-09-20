FROM python:3.10.12-alpine

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./DjangoAPI /app

WORKDIR /app

RUN python manage.py migrate