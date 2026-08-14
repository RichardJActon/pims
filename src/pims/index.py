# index
from flask import (
    Blueprint,
    redirect,
    url_for,
    render_template
) 
from pims.session import *

# index_page = Blueprint('index_page', __name__, static_folder="static", template_folder="templates")
def construct_bp(people, projects):
    bp = Blueprint('index', __name__)

    @bp.route("/")
    def index():
        try:
            # global people
            person = getnormaluser(people)
        except Exception:
            return redirect(url_for("login.login"))
    
        # Get recent projects]
        recent_projects = []
        # global projects
        for project in projects.find({"owner":person["_id"]}).sort("date_created",-1).limit(10):
            recent_projects.append(project)

        return render_template("pages/index.html",person=person, projects=recent_projects)
    return bp
