#!/usr/bin/env python3

from flask import Flask, request, render_template, make_response, url_for, redirect
import random
from urllib.parse import quote_plus
from pymongo import MongoClient
from bson.json_util import dumps
from pathlib import Path
import json
import ldap
import time
import datetime
import os

app = Flask(__name__)

@app.route("/")
def index():
    try:
        person = getnormaluser()
    except Exception:
        return redirect(url_for("login"))
    
    # Get recent projects]
    recent_projects = []
    for project in projects.find({"owner":person["_id"]}).sort("date_created",-1).limit(10):
        recent_projects.append(project)


    return render_template("index.html",person=person, projects=recent_projects)


@app.route("/project/<project_id>")
def project(project_id):

    project_id = int(project_id)

    try:
        person = getnormaluser()
    except Exception:
        return redirect(url_for("login"))

    # Get the project
    project = projects.find_one({"project_id":project_id})

    if not project:
        raise Exception("No project found")
        
    # Check they are allowed to see this
    if not can_person_see_project(person,project):
        raise Exception("Not allowed to view this project")

    # We want to swap the owner on the project for the owner name
    owner = people.find_one({"_id": project["owner"]})
    project["owner"] = owner["name"]

    return render_template("project.html",person=person, project=project)



@app.route("/search")
def search():
    pass

@app.route("/account")
def account():
    pass

@app.route("/editproject",defaults={"project_id":None})
@app.route("/editproject/<project_id>")
def editproject(project_id):
    try:
        person = getnormaluser()
    except Exception:
        return redirect(url_for("login"))

    # They could be starting a new project or editing an existing
    # one.
    project = None

    # If it's a new project they need to be an admin
    if project_id is None and not person["is_admin"]:
        raise Exception("Admins only")

    if project_id is None:
        project = {"id":"","title":"","description":""}
    else:
        project = projects.find_one({"project_id":int(project_id)})
        if not project:
            raise Exception(f"Project {project_id} not found")

        # To do this they either need to be an admin or they need to own the project
        if not can_person_edit_project(person,project):
            raise Exception("You don't have permission to edit this project")


    return render_template("edit_project.html",project=project, person=person)

@app.route("/saveproject", methods = ['POST', 'GET'])
def saveproject():
    "Create a new project or update an existing one"

    person = getnormaluser()
    form = get_form()

    # If there isn't a project id then we're making a new project
    if not form["project_id"]:
        # Only admins can make new projects
        if not person["is_admin"]:
            raise Exception("Only admins can create projects")
        
        # We need an owner
        owner = people.find_one({"username":form["owner"]})["_id"]

        # We need to find the next available project_id
        project_id = 1

        for last_project in projects.find().sort({"project_id":-1}).limit(1):
            project_id = last_project["project_id"] + 1

        new_project = {
            "owner": owner,
            "title": form["title"],
            "description": form["description"],
            "date_created": datetime.datetime.now(tz=datetime.timezone.utc),
            "status": "proposed",
            "samples":[],
            "tags":form["tags"],
            "project_id": project_id,
            "share_codes": [],
            "shared_with": []
        }

        projects.insert_one(new_project)
        return str(project_id)


    else:

        # We're editing an existing project
        project = projects.find_one({"project_id":int(form["project_id"])})

        # Check this person is allowed to do this
        if not can_person_edit_project(person,project):
            raise Exception("You can't edit this project")

        # They may want to change the owner
        if form["owner"]:
            if not (person["is_admin"]):
                raise Exception("Only admins can change owners")
            
            owner = people.find_one({"username":form["owner"]})["_id"]
            if project["owner"] != owner["_id"]:
                # update the owner
                projects.update_one({"_id":project["_id"]},{"$set":{"owner_id":owner["_id"]}})

        # We'll update the title and description
        projects.update_one(
            {"_id":project["_id"]},
            {"$set":{
                "title":form["title"],
                "description":form["description"],
                "tags": form["tags"]
            }})

        return str(project["project_id"])


@app.route("/deletesample", methods = ['POST', 'GET'])
def deletesample():
    "Deletes a sample"

    person = getnormaluser()
    form = get_form()

    # There should always be a project id and a sample id
    project_id = int(form["project_id"])
    sample_id = int(form["sample_id"])

    project = projects.find_one({"project_id":project_id})

    # Check that this person can edit this project
    if not can_person_edit_project(person,project):
        raise Exception("Not allowed to edit this project")
    
    projects.update_one({"project_id":project_id},{"$pull" : {"samples" :{"sample_id":sample_id}}})

    return("OK")



@app.route("/savesample", methods = ['POST', 'GET'])
def savesample():
    "Create a new sample or update an existing one"

    person = getnormaluser()
    form = get_form()

    # There should always be a project id
    project_id = int(form["project_id"])

    project = projects.find_one({"project_id":project_id})

    # Check that this is OK
    if not can_person_edit_project(person,project):
        raise Exception("Not allowed to edit this project")

    # If there isn't a sample id then we're making a new sample
    if not form["sample_id"]:

        # We need to find the next available sample id
        sample_id = 0
        for sample in project["samples"]:
            if sample["sample_id"]>=sample_id:
                sample_id = sample["sample_id"] + 1

        sample = {
            "sample_id": sample_id,
            "name": form["name"],
            "state": form["state"],
            "organism": form["organism"],
            "status": "Not received",
            "tags" : {}
        }
        
        for i,tag in enumerate(project["tags"]):
            sample["tags"][tag] = form["tags"][i]

        projects.update_one({"project_id":project_id},{"$push":{"samples":sample}})
        return "OK"
    
    else:
        sample_id = int(form["sample_id"])

        sample = {
            "samples.$.name": form["name"],
            "samples.$.state": form["state"],
            "samples.$.organism": form["organism"],
            "samples.$.status": "Not received",
            "samples.$.tags" : {}
        }

        for i,tag in enumerate(project["tags"]):
            sample["samples.$.tags"][tag] = form["tags"][i]

        projects.update_one({"project_id":project_id, "samples.sample_id":sample_id},{"$set": sample})
        return "OK"



@app.route("/reports")
def reports():
    pass

@app.route("/checkowner", methods = ['POST', 'GET'])
def checkowner():
    "Used to check usernames for new projects when they press the check button"
    # This is for admins only
    getadminuser()

    form = get_form()

    found_person = people.find_one({"username":form["username"]})

    person_text = f"{found_person['name']} ({form['username']})"

    return person_text



@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/processlogin", methods = ['POST', 'GET'])
def process_login():
    """
    Validates an username / password combination and generates
    a session id to authenticate them in future

    @username:  Their BI username
    @password:  The unhashed version of their password

    @returns:   Forwards the session code to the json response
    """
    form = get_form()
    username = form["username"]
    password = form["password"]

    # We might not try the authentication for a couple of reasons
    # 
    # 1. We might have blocked this IP for too many failed logins
    # 2. We might have locked this account for too many failed logins

    # Calculate when any timeout ban would have to have started so that
    # it's expired now
    timeout_time = int(time.time())-(60*(int(server_conf["security"]["lockout_time_mins"])))


    # We'll check the IP first
    ip = ips.find_one({"ip":request.remote_addr})
    
    if ip and len(ip["failed_logins"])>=server_conf["security"]["failed_logins_per_ip"]:
        # Find if they've served the timeout
        last_time = ip["failed_logins"][-1]

        if last_time < timeout_time:
            # They've served their time so remove the records of failures
            ips.update_one({"ip":request.remote_addr},{"$set":{"failed_logins":[]}})

        else:
            raise Exception("IP block timeout")

    # See if we have a record of failed logins for this user
    person = people.find_one({"username":username})

    if person and person["locked_at"]:
        if person["locked_at"] > timeout_time:
            # Their account is locked
            raise Exception("User account locked")
        else:
            # They've served their time, so remove the lock
            # and failed logins
            people.update_one({"username":username},{"$set":{"locked_at":0}})
            people.update_one({"username":username},{"$set":{"failed_logins":[]}})


    # Check the password against AD
    conn = ldap.initialize("ldap://"+server_conf["server"]["ldap"])
    conn.set_option(ldap.OPT_REFERRALS, 0)

    # bypass auth
    response = make_response(sessioncode)
    response.set_cookie("pims_session_id",sessioncode)
    return(response)

    try:    
        conn.simple_bind_s(username+"@"+server_conf["server"]["ldap"], password)

        # Clear any IP recorded login fails
        ips.delete_one({"ip":request.remote_addr})

        sessioncode = generate_id(20)


        if not person:
            # We're making a new person.  We can therefore query AD
            # to get their proper name and email.

            # We can theoretically look anyone up, but this filter says
            # that we're only interested in the person who logged in
            filter = f"(&(sAMAccountName={username}))"

            # The values we want to retrive are their real name (not 
            # split by first and last) and their email
            search_attribute = ["distinguishedName","mail"]

            # This does the search and gives us back a search ID (number)
            # which we can then use to fetch the result data structure
            dc_string = ",".join(["DC="+x for x in server_conf["server"]["ldap"].split(".")])
            res = conn.search(dc_string,ldap.SCOPE_SUBTREE, filter, search_attribute)
            answer = conn.result(res,0)

            # We can then pull the relevant fields from the results
            name = answer[1][0][1]["distinguishedName"][0].decode("utf8").split(",")[0].replace("CN=","")
            email = answer[1][0][1]["mail"][0].decode("utf8")

            # Now we can make the database entry for them
            new_person = {
                "username": username,
                "name": name,
                "email": email,
                "disabled": False,
                "sessioncode": "",
                "locked_at": 0,
                "failed_logins": [],
                "is_admin": False
            }
        
            people.insert_one(new_person)

        # We can assign the new sessioncode to them and then return it
        people.update_one({"username":username},{"$set":{"sessioncode": sessioncode}})

        response = make_response(sessioncode)
        response.set_cookie("pims_session_id",sessioncode)
        return(response)
    
    except ldap.INVALID_CREDENTIALS:
        # We need to record this failure.  If there is a user with this name we record
        # against that.  If not then we just record against the IP
        if person:
            people.update_one({"username":username},{"$push":{"failed_logins":int(time.time())}})
            if len(person["failed_logins"])+1 >= server_conf["security"]["failed_logins_per_user"]:
                # We need to lock their account
                people.update_one({"username":username},{"$set":{"locked_at":int(time.time())}})
                


        if not ip:
            ips.insert_one({"ip":request.remote_addr,"failed_logins":[]})

        ips.update_one({"ip":request.remote_addr},{"$push":{"failed_logins":int(time.time())}})

        raise Exception("Incorrect Username/Password from LDAP")

@app.route("/validate_session", methods = ['POST', 'GET'])
def validate_session():
    form = get_form()
    person = checksession(form["session"])
    return(str(person["name"]))


@app.route("/get_user_data", methods = ['POST', 'GET'])
def get_user_data():
    form = get_form()
    person = checksession(form["session"])

    return jsonify(person)


def get_form():
    # In addition to the main arguments we also add the session
    # string from the cookie
    session = ""

    if "pims_session_id" in request.cookies:
        session = request.cookies["pims_session_id"]

    if request.method == "GET":
        form = args_to_dict(request.args)
        form["session"] = session
        return form

    elif request.method == "POST":
        form = args_to_dict(request.form)
        form["session"] = session
        return form

def args_to_dict(args):
    form = {}

    for key in args.keys():
        if key.endswith("[]"):
            form[key[:-2]] = args.getlist(key)
        else:
            form[key] = args.get(key)

    return form

def generate_id(size):
    """
    Generic function used for creating IDs.  Makes random IDs
    just using uppercase letters

    @size:    The length of ID to generate

    @returns: A random ID of the requested size
    """
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    code = ""

    for _ in range(size):
        code += random.choice(letters)

    return code

def getnormaluser():
    form = get_form()
    person = checksession(form["session"])

    return person

def getadminuser():
    form = get_form()
    person = checksession(form["session"])

    if not person["is_admin"]:
        raise Exception("Not and admin")

    return person

def can_person_see_project(person,project):
    if person["is_admin"]:
        return True
    
    if person["_id"] == project["owner"]:
        return True
    
    # We'll do some checking for sharing eventually.

    return False

def can_person_edit_project(person,project):
    if person["is_admin"]:
        return True
    
    if person["_id"] == project["owner"]:
        return True
    
    return False


def checksession (sessioncode):
    """
    Validates a session code and retrieves a person document

    @sessioncode : The session code from the browser cookie

    @returns:      The document for the person associated with this session
    """

    person = people.find_one({"sessioncode":sessioncode})

    if "disabled" in person and person["disabled"]:
        raise Exception("Account disabled")

    if person:
        return person

    raise Exception("Couldn't validate session")



def jsonify(data):
    # This is a function which deals with the bson structures
    # specifically ObjectID which can't auto convert to json 
    # and will make a flask response object from it.
    response = make_response(dumps(data))
    response.content_type = 'application/json'

    return response

def get_server_configuration():
    with open(Path(__file__).resolve().parent.parent / "configuration/conf.json") as infh:
        conf = json.loads(infh.read())
        conf['server']['username'] = os.environ['MONGO_ROOT_USER']
        conf['server']['password'] = os.environ['MONGO_ROOT_PWD']
    return conf


def connect_to_database(conf):

    client = MongoClient(
        conf['server']['address'],
        username = conf['server']['username'],
        password = conf['server']['password'],
        authSource = "pims_database"
    )


    db = client.pims_database

    global people
    people = db.people_collection

    global ips
    ips = db.ips_collection

    global projects
    projects = db.projects_collection

# Read the main configuration
server_conf = get_server_configuration()

# Connect to the database
connect_to_database(server_conf)


