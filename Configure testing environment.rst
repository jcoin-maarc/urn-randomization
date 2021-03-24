Initial setup
#############

Install required packages
*************************

Create a conda or virtual environment and install the packages in requirements.txt

``conda create --name my-env-name --file requirements.txt``

Generating dummy data
*********************

* Set ``PYTHONPATH``

``export PYTHONPATH=.``

* Generate dummy data

``python urand/cli.py -s "CHS JCOIN" dummy-study``

Running flask app
*****************

* Create a new file, `.env` in the project root folder and add the below contents. For the time being, substitute `your_api_key` with any text.

`URN_API_KEY="your_api_aky"`

* Starting the app from command line

``FLASK_APP=urand_gui/app.py flask run``

* API access information is in ``notebooks/urn-randomizer API calls.ipynb``

