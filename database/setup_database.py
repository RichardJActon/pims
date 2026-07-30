#!/usr/bin/env python3
import json
from pymongo import MongoClient
from pathlib import Path
from urllib.parse import quote_plus
import os

def main():
    # Set up the database connection
    with open(Path(__file__).parent.parent / "configuration/conf.json") as infh:
        conf = json.loads(infh.read())

    print("Server",quote_plus(conf['server']['address']))
    print("Username",quote_plus(os.environ['MONGO_PIMS_USER']))
    print("Password",quote_plus(os.environ['MONGO_PIMS_USER_PWD']))

    client = MongoClient(
        conf['server']['address'],
        username = os.environ['MONGO_PIMS_USER'],
        password = os.environ['MONGO_PIMS_USER_PWD'],
        # authSource = "pims_database"
        authSource = "admin"
    )
    
    print("Defined Client")
    db = client.pims_database
    print("create pims_database")
    
    # We have a collection for the users called "people"
    global people
    people = db.people_collection
    print("Create people collection")
    # We have a collection of IPs which we use for rate limiting
    # and blocking
    global ips
    ips = db.ips_collection
    ips.insert_one(dict(demo = "255.255.255.255"))
    print("Create ips collection")

    # Remove everything so we're starting fresh
    # people.delete_many({})
    # print("clear people")
    # ips.delete_many({})
    # print("clear ips")

if __name__ == "__main__":
    main()
