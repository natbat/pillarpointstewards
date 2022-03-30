#!/bin/bash
export DATABASE_URL="postgresql://localhost/pillarpointstewards"
./pillarpointstewards/manage.py "$@"
