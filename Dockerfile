FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY pillarpointstewards .

RUN python manage.py collectstatic --noinput

EXPOSE 8080

CMD bash -c "/app/manage.py migrate && gunicorn --bind :8000 --workers 2 config.wsgi"
