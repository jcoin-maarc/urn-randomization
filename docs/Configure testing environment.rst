Initial setup
#############

Install required packages
*************************

Create a conda or virtual environment and install the packages in requirements.txt

``conda create --name my-env-name python=3.9``

``conda activate my-env-name``

``pip install -r requirements.txt``

``pip uninstall datatables sqlalchemy-datatables``

``pip install sqlalchemy-datatables``

``pip uninstall Flask-Bootstrap``


Adding users
************

Google OAuth setup
==================
This app uses google OAuth for login.

Get OAuth credentials from Google
-----------------------------------------

Visit the Google Developers Console at https://console.developers.google.com
and create a new project. In the "APIs & auth" section, click on "Credentials",
and then click the "Create a new Client ID" button. Select "Web Application"
for the application type, and click the "Configure consent screen" button.
Put in your application information, and click Save. Once you’ve done that,
you’ll see two new fields: "Authorized JavaScript origins" and
"Authorized redirect URIs". Set authorized javascript origin to http://localhost:5000/ and
Set the authorized redirect URI to http://localhost:5000/login/google/authorized,
and click "Create Client ID". Google will give you a client ID and client secret.

Set environment variables
-------------------------
Example env file is available in the project root folder. You can save it as `.env' in the project folder with
your values. You'll need to set the following environment variables:

GOOGLE_OAUTH_CLIENT_ID: set this to the client ID
you got from Google.


GOOGLE_OAUTH_CLIENT_SECRET: set this to the client secret
you got from Google.


OAUTHLIB_RELAX_TOKEN_SCOPE: set this to true. This indicates that
it's OK for Google to return different OAuth scopes than requested; Google
does that sometimes


OAUTHLIB_INSECURE_TRANSPORT: set this to true. This indicates that
you're doing local testing, and it's OK to use HTTP instead of HTTPS for
OAuth. You should only do this for local testing.
Do not set this in production!


Generating dummy data/ adding users
*********************

* Set ``PYTHONPATH``

``export PYTHONPATH=.``

Adding users
============

* Initialize flask app DB with available studies & create user tables

``flask create_db``

* Users for the Urn Randomization app can only be added via its command line interface. Use the below command to add users

``flask add_user UNAME EMAIL``

* To view list of users and their API keys,

``flask list_users``

Use the above command to get API key corresponding to your username and update your `.env` file with it.

Generate dummy data
===================

``python urand/cli.py -s "CHS JCOIN HUB" dummy-study``

Running flask app
*****************

* Starting the app from command line

``flask run``

* API access information is in ``notebooks/urn-randomizer API calls.ipynb``

