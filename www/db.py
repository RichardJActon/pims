from pymongo.database import Database
import imp
from pymongo import MongoClient
import json
from pathlib import Path
import os
from typing import Any, Dict

def get_server_configuration(config_path: str = "configuration/conf.json") -> Dict:
    """
    Path is specified relative to the project root directory
    Reads configuration from the configuration file
    
    Secrets can be supplied via this file but ideally should not be
    unless the entire file is supplied via a secrets mangement system such as SOPS

    Environment variables will take precedence over the config file if they
    are defined.

    Environment variables:
    
    MONGO_PIMS_USER
    MONGO_PIMS_USER_PWD

    :param config_path: path, relative to project root, of the config file
    :type config_path: str
    :return: Dictionary of configuration information
    :rtype: dict
    """
    
    # with open(Path(__file__).resolve().parent.parent / "configuration/conf.json") as infh:
    with open(Path().resolve().parent / "configuration/conf.json") as infh:
        conf = json.loads(infh.read())

    # conf['server']['username'] = os.environ['MONGO_ROOT_USER']
    # conf['server']['password'] = os.environ['MONGO_ROOT_PWD']
    try:
        conf['server']['username'] = os.environ['MONGO_PIMS_USER']
    except:
        pass
    
    try:
        conf['server']['password'] = os.environ['MONGO_PIMS_USER_PWD']
    except:
        pass
    
    return conf

def connect_to_database(conf) -> Database[dict[str, Any]]:
    """
        
    """
    client: MongoClient[Dict[str, Any]] = MongoClient(
        host = conf['server']['address'],
        port = conf['server']['port'],
        username = conf['server']['username'],
        password = conf['server']['password'],
        authSource = conf['server']['auth_source']
        # port = 27017,
        # username = None,
        # password = None,
    )
    db = client.pims_database
    return db


# Read the main configuration
server_conf = get_server_configuration()

# Connect to the database
db = connect_to_database(server_conf)

people = db.people_collection
ips = db.ips_collection
projects = db.projects_collection
