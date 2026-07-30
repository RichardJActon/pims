from flask import Blueprint, redirect, url_for, render_template
from session import *
from db import *

index_page = Blueprint('index_page', __name__, static_folder="static", template_folder="templates")

@index_page.route("/")
def index():
    try:
        global people
        person = getnormaluser(people)
    except Exception:
        return redirect(url_for("login.login"))
    
    # Get recent projects]
    recent_projects = []
    global projects
    for project in projects.find({"owner":person["_id"]}).sort("date_created",-1).limit(10):
        recent_projects.append(project)

    return render_template("index.html",person=person, projects=recent_projects)
