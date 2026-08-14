from pymongo import MongoClient
from pymongo.database import Database
from typing import Any, Dict
# import imp
# import json
# from pathlib import Path
# import os

def connect_to_database(conf) -> Database[dict[str, Any]]:
    """
    Connect to the MongoDB istance with the details provided in the application
    config
    """
    client: MongoClient[Dict[str, Any]] = MongoClient(
        host = conf['HOST'],
        port = conf['PORT'],
        username = conf['USER'],
        password = conf['PWD'],
        authSource = conf['AUTH_SOURCE']
    )
    db = client[conf["DATABASE"]]
    return db

