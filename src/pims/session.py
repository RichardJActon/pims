from flask import request, current_app, session
import random
from pims.utility import args_to_dict
# from pims.logging_utils import app_exception_logging
import ldap # move to ldap3? - better docs # move to ldap3? - better docs
import time
import typing
from typing import (
    Dict,
    Any,
)
from datetime import (
    datetime,
    timezone,
)

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

# @app_exception_logging
def checksession (sessioncode: str, people) -> Dict[str, Any]:
    """
    Validates a session code and retrieves a person document

    :param sessioncode: The session code from the browser cookie

    :return: The document for the person associated with this session
    """
    
    person = people.find_one({"sessioncode":sessioncode})
    try:
        if person is None:
            raise Exception("Person not found for this session")
    except Exception as e:
        current_app.logger.exception(e)

    try:
        if "disabled" in person and person["disabled"]:
            raise Exception("Account disabled")
    except Exception as e:
        current_app.logger.exception(str(e))

    # if person:
    #     return person
    # else:
    #     raise Exception("Couldn't validate session")
        
    try:
        if person:
            return person
    except:
        current_app.logger.exception("Couldn't validate session")
    # Exception("Couldn't validate session")

def getnormaluser(people):
    # form = get_form()
    # person = checksession(form["session"], people)
    
    user_query = {"username": session["user"]["preferred_username"]}
    person = people.find_one(user_query)

    return person

def getadminuser(people):
    # form = get_form()
    # person = checksession(form["session"], people)

    user_query = {"username": session["user"]["preferred_username"]}
    person = people.find_one(user_query)

    if not person["is_admin"]:
        raise Exception("Not and admin")

    return person

def generate_id(size: int) -> str:
    """
    Generic function used for creating IDs.  Makes random IDs
    just using uppercase letters

    :param size:    The length of ID to generate
    :size type: int
    :return: A random ID of the requested size
    :rtype: str
    """
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    code = ""
    for _ in range(size):
        code += random.choice(letters)
    return code

def make_new_person(
    people,
    userinfo
    # username: str,
    # name: str = "",
    # email: str = ""
):
    """
    Make a new person in mongoDB.
    
    When making an entry to track unauthenticated login attempts to block
    IPs that make repeated login attempts fills in name with username and
    a <username>@example.com email address.
    This is done when name and email are not provided.
    
    :param people: MongoDB people collection object
    :param userinfo: user information from the Oauth/OIDC token
    
    """
    # :param username:
    # :type username: str
    # :param name:
    # :type name: str
    # :param email:
    # :type email: str
    username = userinfo["preferred_username"]
    
    if userinfo.get("email") is None:
        email = userinfo.get("preferred_username") + "@example.com"

    name = str(userinfo.get('given_name')  or '') + ' ' + str(userinfo.get('family_name') or '')
    if name == "":
        name = username

    new_person = {
        "username": username,
        "name": name,
        "email": email,
        "email_verified": bool(userinfo.get("email_verified") or False),
        "disabled": False,
        "date_created": datetime.now(tz = timezone.utc),
        "last_authenticated": datetime.fromtimestamp(userinfo.get("auth_time"), tz = timezone.utc),
        "sessioncode": "",
        "locked_at": 0,
        "failed_logins": [],
        "is_admin": False
    }
    try:
        people.insert_one(new_person)
    except:
        current_app.logger.exception("Failed to create new person!")



# def new_person_from_ldap(people, username, server_conf, conn):
#     # We're making a new person.  We can therefore query AD
#     # to get their proper name and email.
#     # We can theoretically look anyone up, but this filter says
#     # that we're only interested in the person who logged in
#     filter = f"(&(sAMAccountName={username}))"

#     # The values we want to retrive are their real name (not 
#     # split by first and last) and their email
#     search_attribute = ["distinguishedName","mail"]

#     # This does the search and gives us back a search ID (number)
#     # which we can then use to fetch the result data structure
#     dc_string = ",".join(["DC="+x for x in server_conf["server"]["ldap"].split(".")])
#     res = conn.search(dc_string,ldap.SCOPE_SUBTREE, filter, search_attribute)
#     answer = conn.result(res,0)

#     # We can then pull the relevant fields from the results
#     name = answer[1][0][1]["distinguishedName"][0].decode("utf8").split(",")[0].replace("CN=","")
#     email = answer[1][0][1]["mail"][0].decode("utf8")

#     make_new_person(people, username, name, email)




# We might not try the authentication for a couple of reasons
# 
# 1. We might have blocked this IP for too many failed logins
# 2. We might have locked this account for too many failed logins
# 
# Calculate when any timeout ban would have to have started so that
# it's expired now
#
# def ip_lockout(people, username, ips, lockout_time_mins: int, failed_logins_per_ip: int) -> None:
#     # Calculate when any timeout ban would have to have started so that
#     # it's expired now
#     # !! make lockout time configurable? !!
#     timeout_time = int(time.time()) - (60 * lockout_time_mins)
#     ip = ips.find_one({"ip":request.remote_addr})
#     failed_logins = ip["failed_logins"]
    
#     if failed_logins >= failed_logins_per_ip:
#         # Find if they've served the timeout
#         last_time = ip["failed_logins"][-1]

#         try:
#             if last_time < timeout_time:
#                 # They've served their time so remove the records of failures
#                 ips.update_one({"ip":request.remote_addr},{"$set":{"failed_logins":[]}})
#                 # 
#             else:
#                 raise Exception("IP block timeout")
#         except Exception as e:
#             current_app.logger.exception(e)
            
#         # See if we have a record of failed logins for this user
#         person = people.find_one({"username":username})
#     try:
#         if person and person["locked_at"]:
#             if person["locked_at"] > timeout_time:
#                 # Their account is locked
#                 raise Exception("User account locked")
#             else:
#                 # They've served their time, so remove the lock
#                 # and failed logins
#                 people.update_one({"username":username},{"$set":{"locked_at":0}})
#                 people.update_one({"username":username},{"$set":{"failed_logins":[]}})
#     except Exception as e:
#         current_app.logger.exception(e)

