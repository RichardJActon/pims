#!/usr/bin/env python3

from flask import Flask, request, render_template, make_response, url_for, redirect
from urllib.parse import quote_plus
from pymongo import MongoClient
from pathlib import Path
import json
import datetime

from index import index_page
from login import loginb, process_loginb, validate_sessionb, get_user_datab
from session import *
from db import *

app = Flask(__name__)

app.register_blueprint(index_page)
app.register_blueprint(loginb)
app.register_blueprint(process_loginb)
app.register_blueprint(validate_sessionb)
app.register_blueprint(get_user_datab)

@app.route("/project/<project_id>")
def project(project_id):

    project_id = int(project_id)

    try:
        person = getnormaluser(people)
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
        person = getnormaluser(people)
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

@app.route("/saveproject", methods = ['POST', 'GET'])
def saveproject():
    "Create a new project or update an existing one"

    person = getnormaluser(people)
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

    person = getnormaluser(people)
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

    person = getnormaluser(people)
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
    getadminuser(people)

    form = get_form()

    found_person = people.find_one({"username":form["username"]})

    person_text = f"{found_person['name']} ({form['username']})"

    return person_text

