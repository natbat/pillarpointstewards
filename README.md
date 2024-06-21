# pillarpointstewards

https://www.pillarpointstewards.com/

Login via Auth0: https://www.pillarpointstewards.com/login/

### Development environment is GitHub Codespaces

Before launching Codespaces you'll need to configure these Codespaces secrets using the interface at https://github.com/settings/codespaces

- `AUTH0_CLIENT_SECRET` - get [from Auth0](https://manage.auth0.com/dashboard/us/pillarpointstewards/applications/DLXBMPbtamC2STUyV7R6OFJFDsSTHqEA/settings)
- `AUTH0_FORWARD_URL`: `https://www.pillarpointstewards.com/auth0-callback/`
- `AUTH0_FORWARD_SECRET`: get from Simon's 1Password
- `ALLOWED_HOSTS_STAR`: `1`

Having set those secrets for the `natbat/pillarpointstewards` repo you can launch a Codespaces environment against that repo.

After a few minutes of automated setup this should start a development server. You can access that from the ports menu by clicking the little Globe icon that shows up when you hover over the port 8000 (Application) entry:

![CleanShot 2023-08-17 at 11 44 49@2x](https://github.com/natbat/pillarpointstewards/assets/9599/e34582d9-9939-4658-a27a-8e448c843849)

Now you should **sign in with your Google account** to create a user.

To upgrade that user to an admin, start a new terminal window running and run this command:

```bash
./manage.sh shell_plus
```
Then in the Python console run these:
```python
User.objects.update(is_active=True, is_staff=True, is_superuser=True)
# And to get the shift calculator working:
TidePrediction.populate_for_station(9414131)
```

### Running the tests

Run this in a terminal window:

    pytest pillarpointstewards

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

- Pattern portfolio: https://www.pillarpointstewards.com/patterns/
- Admin timeline showing various actions around the site: https://www.pillarpointstewards.com/admin/timeline/ - http://127.0.0.1:8000/admin/timeline/
- Sentry errors for production: https://sentry.io/organizations/pillar-point-stewards/issues/?project=6304204

# Fragments

Some site content - such as emergency contact phone numbers - is held in the database to avoid sharing it in a public GitHub repository.

The `contact_details_$team-slug` fragments show contact details and are displayed on the logged-in homepage for each team.

Content for these needs to be copied and pasted into new databases - we keep those in the private repository [pillarpointstewards-private](https://github.com/natbat/pillarpointstewards-private).

They can be edited at `/admin/homepage/fragment/`.
