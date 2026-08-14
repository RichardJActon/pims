#!/usr/bin/env python3

# from flask import Flask, request, render_template, make_response, url_for, redirect
# from urllib.parse import quote_plus
# from pymongo import MongoClient
# from pathlib import Path
# import json
# import datetime

from flask import Flask
from pims import (
    index,
    login,
    session,
    pages,
    db,
)
# from pims.login import *
import os
import json
import logging
from pathlib import Path

def create_app():
    app = Flask(__name__)
    logging.basicConfig(
        format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    config_path = "configuration/config.json"
    default_config_path_used = False
    try:
        config_path = os.environ["PIMS_CONFIG_PATH"]
    except:
        default_config_path_used = True

    # Read the main configuration
    app.config.from_file(Path().absolute() / config_path, load=json.load)
    # Read any environment variables which might overrule the config file
    # NB all env vars prefixed "PIMS_X" are available in app.config["X"]
    # For nested config env vars take the form: "PIMS__SUB__X" app.config["SUB"]["x"]
    app.config.from_prefixed_env(prefix="PIMS_")

    if default_config_path_used:
        app.logger.info("PIMS_CONFIG_PATH not set using default path 'configuration/config.json'")

    # Connect to the database
    dbc = db.connect_to_database(app.config["MONGO"])

    # Declare widely used collections
    people = dbc.people_collection
    ips = dbc.ips_collection
    projects = dbc.projects_collection

    # Blueprint constructors
    app.register_blueprint(index.construct_bp(people, projects))
    app.register_blueprint(login.construct_bp(people, projects, ips))
    app.register_blueprint(pages.construct_bp(people, projects))
    
    # app.register_blueprint(pages.bp)
    return app

