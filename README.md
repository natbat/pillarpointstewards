# pillarpointstewards

https://www.pillarpointstewards.com/

Login via Auth0: https://www.pillarpointstewards.com/login/

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

### Running the tests

    pytest pillarpointstewards

### Running management commands

The `./manage.sh` script sets the correct environment variables for development and runs management commands, for example:

    ./manage.sh shell_plus
    ./manage.py makemigrations

### Creating a superuser for the Django admin

    ./manage.sh createsuperuser

Even better, sign in with Auth0 and run the following to upgrade your account to a super user:

```
./manage.sh shell_plus
>>> User.objects.update(is_active=True, is_staff=True, is_superuser=True)
```

### Handling requirements

Requirements are listed in the `requirements.in` file. These are then pinned in `requirements.txt`. To update `requirements.txt` from `requirements.in` run the following in the project's virtual environment:

    pip install pip-tools
    pip-compile --upgrade --generate-hashes requirements.in

The `--upgrade` flag causes it to check PyPI for any upgraded versions of packages that still match the line in `requirements.in`. `--generate-hashes` adds hashes.

This command will over-write `requirements.txt` with the new pinned versions.

To upgrade your local virtual environment to the exact versions of the packages recorded in `requirements.txt` run the other command that was installed by `pip-tools`:

    pip-sync

## Where the code is

- CSS: [pillarpointstewards/static/main.css](pillarpointstewards/static/main.css)
- Homepage template: [pillarpointstewards/templates/index.html](pillarpointstewards/templates/index.html)

## Useful URLs

- Pattern portfolio: https://www.pillarpointstewards.com/patterns/ - http://127.0.0.1:8000/patterns/
- Admin timeline showing various actions around the site: https://www.pillarpointstewards.com/admin/timeline/ - http://127.0.0.1:8000/admin/timeline/
- Sentry errors for production: https://sentry.io/organizations/pillar-point-stewards/issues/?project=6304204

# Fragments

Some site content - such as emergency contact phone numbers - is held in the database to avoid sharing it in a public GitHub repository.

The `contact_details` fragment shows contact details and is displayed on the logged-in homepage.

Content for these needs to be copiend and pasted into new databases - we keep those in the private repository [pillarpointstewards-private](https://github.com/natbat/pillarpointstewards-private).

They can be edited at `/admin/homepage/fragment/`.
