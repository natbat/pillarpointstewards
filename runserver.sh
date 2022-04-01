#!/bin/bash
export DATABASE_URL="postgresql://localhost/pillarpointstewards"
export DJANGO_DEBUG=1
./pillarpointstewards/manage.py migrate
./pillarpointstewards/manage.py runserver
