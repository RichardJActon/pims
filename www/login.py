from flask import Blueprint, render_template, make_response
from session import *
from db import *

import random
from bson.json_util import dumps
import time
import ldap # move to ldap3? - better docs # move to ldap3? - better docs

# login = Blueprint('login', __name__)
loginb = Blueprint('login', __name__, static_folder="static", template_folder="templates")

@loginb.route("/login")
def login():
    return render_template("login.html")

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

process_loginb = Blueprint('process_login', __name__)

@process_loginb.route("/processlogin", methods = ['POST', 'GET'])
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

    testing_no_auth = True
    if testing_no_auth:
        sessioncode = generate_id(20)
        response = make_response(sessioncode)
        response.set_cookie("pims_session_id",sessioncode)
        global people
        person = people.find_one({"username":username})
        if not person:
            name  = username
            email = username + "@example.com"
            print("NOT PERSON - MAKING NEW!")

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

        people.update_one({"username":username},{"$set":{"sessioncode": sessioncode}})
        return(response)
    else: 
        # We might not try the authentication for a couple of reasons
        # 
        # 1. We might have blocked this IP for too many failed logins
        # 2. We might have locked this account for too many failed logins

        # Calculate when any timeout ban would have to have started so that
        # it's expired now
        #
        # !! server_conf ?
        timeout_time = int(time.time())-(60*(int(server_conf["security"]["lockout_time_mins"])))


        # We'll check the IP first
        global ips
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

validate_sessionb = Blueprint('validate_session', __name__)

@validate_sessionb.route("/validate_session", methods = ['POST', 'GET'])
def validate_session():
    form = get_form()
    global people
    person = checksession(form["session"], people)
    return(str(person["name"]))


def jsonify(data):
    # This is a function which deals with the bson structures
    # specifically ObjectID which can't auto convert to json 
    # and will make a flask response object from it.
    response = make_response(dumps(data))
    response.content_type = 'application/json'

    return response

get_user_datab = Blueprint('get_user_data', __name__)

@get_user_datab.route("/get_user_data", methods = ['POST', 'GET'])
def get_user_data():
    form = get_form()
    global people
    person = checksession(form["session"], people)

    return jsonify(person)




