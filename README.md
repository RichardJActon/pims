# Proteomics LIMS system (PIMS)

This is a starting point for new web resources on our site.

It provides a basic setup of a flask app with bootstrap templates and a mongo db backend.
It handles user logins linked initially to an LDAP server.

Using this code
===============

To work with this you need to clone this repository.

```
git clone https://github.com/RichardJActon/pims.git
cd pims
```

Changes to make
===============

A number of things have been set up with values that you'll need to change.

Database details
----------------

The system uses a mongo-db database.  The database name and login details must be changed

In ```database/create_database_and_user.txt``` you need to change the name of the database in both the use statement and the createuser.  You also need to change the username and password

You need to create a ```configuration/conf.json``` file from the ```example_conf.json``` template where you input the address, username and password, which must match the ones above.

In the ```database/setup_database.py``` script you'll need to change the name of the database and the collections you want to use.

Cookie Name
-----------

You'll need to select a name for your session cookie.
This will be set in the ```www/static/js/main.js``` file in all of the ```Cookies.set Cookies.get Cookies.remove``` statements


Setting up the system
=====================

Once you've made the changes above you can follow the steps below to create a working base system from which you can develop.

Create a venv
-------------

From the root of the repository

You'll also need to download and install a binary python-ldap whl from https://www.lfd.uci.edu/~gohlke/pythonlibs/

On linux

```
python -m venv venv
. venv/Scripts/activate
pip install -r requirements.txt
pip install python-ldap 
```

Create the database
-------------------

You'll need to have mongodb installed and know how to get to a root shell.

Copy the text from ```database/create_database_and_user.txt``` into the shell to create your basic setup.  Beware that mongosh on windows has a bug where some lines of copied text get lost during pasting so you might need to copy/paste one line at a time, which is annoying.

Once that's done run ```database/setup_database.py``` to check the connection and set up the collections you are going to use.

*as mongo creates these entries on the fly setup-databases does not appear to do anything unless the globals are to make the db objects available somewhere else in the app? - alternatively clearing the database to start with it empty*

Start the app
-------------

From the shell in which you started the venv

Move to the ```www``` folder

```
flask --debug --app pims.py run
```

This should start the server and you should have a basic system running on 127.0.0.1:5000

You should change the name in this to whatever you changed your app name to.

# Automated Testing

To run tests using the following command in the route directory

```
pytest --doctest-modules --ignore data --ignore database
```

(NB - couldn't get the ignore directories in their pyproject.toml so invoking them directly)

# Building Documentation

The documentation in generated with sphinx, source files can be found in `docs/source`

In `docs` run:

```
make html
```

To generate the documentation locally in `docs/build` this directory is ignored
Built documentation is not to be committed to the repo a CI action will build and deploy it from what is pushed to the githost

# Qs

- Details of babraham LDAP config - would like to replicate the basics in testing env
- config in XDG config?

- sphinx docs
- pytest

- json schema validation on mongo
- capture "version of app that last modified entry" in DB

- ? explore moving to flask session management
    encrypted session cookie, expiry options etc.


# Style notes

- when importing multiple functions explicitly from a module they should be listed one per line and the last should have a tailing comma

```
# from x import q w
from x import (
  q,
  w,
)
```

When imports are changed this makes for cleaner easier to read and diffs and git commits 


