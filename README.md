# pillarpointstewards

https://www.pillarpointstewards.com/

## Local development environment

You'll need Python 3 and PostgreSQL - I recommend using [Postgres.app](https://postgresapp.com/).

Create a local database called `pillarpointstewards`.

Open `Postgres.app`, double click on the `postgres` database, then type the following at the prompt:

    create database pillarpointstewards;

It should look like this:
```
postgres=# create database pillarpointstewards;
CREATE DATABASE
```

In the local checkout of the repo, create a new Python virtual environmet like this:

    python3 -m venv venv

Activate the virtual environment:

    source venv/bin/activate

Install (or upgrade) the dependencies from `requirements.txt`:

    python -m pip install -r requirements.txt

Start the development server, which will also run any database migrations:

    ./runserver.sh

### Running management commands

The `./manage.sh` script sets the correct environment variables for development and runs management commands, for example:

    ./manage.sh shell_plus
    ./manage.py makemigrations

### Creating a superuser for the Django admin

    ./manage.sh createsuperuser

Follow the prompts. You can leave email blank.
