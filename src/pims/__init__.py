#!/usr/bin/env python3
from flask import Flask
from pims import (
    index,
    login,
    session,
    pages,
    db,
    auth,
)
# from pims.login import *
import os
import json
import logging
from pathlib import Path
from authlib.integrations.flask_client import OAuth
from pprint import pprint
# from pims.logging_utils import exception_logging

def create_app():
    app = Flask(__name__)
    logging.basicConfig(
        format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # app_exception_logging = partial(exception_logging, logger = current_app.logger)

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
    # For nested config env vars take the form: "PIMS_SUB__X" app.config["SUB"]["x"]
    app.config.from_prefixed_env(prefix="PIMS")
    
    if default_config_path_used:
        app.logger.info("PIMS_CONFIG_PATH not set using default path 'configuration/config.json'")

    try:
        if app.config["SECRET_KEY"] is None:
            raise Exception("Flask cookie secret not set!")
    except Exception as e:
        app.logger.error(str(e))

    # print complete config to log for debugging
    # app.logger.info(pprint(dict(app.config.items())))
     
    oauth = OAuth(app)
    # oauth.register(
    #     name = "testing",
    #     # "authorize_url": "http://localhost:8080/realms/testrealm/protocol/openid-connect/auth",
    #     client_id = app.config["OAUTH_ENDPOINTS"]["testing"]['client_id'],
    #     client_secret = app.config["OAUTH_ENDPOINTS"]["testing"]['client_secret'],
    #     server_metadata_url = app.config["OAUTH_ENDPOINTS"]["testing"]['server_metadata_url'],
    #     client_kwargs = {"scope": "openid email profile"}
    # )
    auth.register_oauth_endpoints(oauth, app.config["OAUTH_ENDPOINTS"])
    oauth_providers = [*app.config["OAUTH_ENDPOINTS"]]
    
    # Connect to the database
    dbc = db.connect_to_database(app.config["MONGO"])

    # Declare widely used collections
    people = dbc.people_collection
    ips = dbc.ips_collection
    projects = dbc.projects_collection

    # Blueprint constructors
    app.register_blueprint(index.construct_bp(people, projects))
    app.register_blueprint(login.construct_bp(people, projects, ips, oauth, oauth_providers))
    app.register_blueprint(pages.construct_bp(people, projects))
    
    # app.register_blueprint(pages.bp)
    return app

