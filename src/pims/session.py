from flask import request, current_app
import random
from pims.utility import args_to_dict
import ldap # move to ldap3? - better docs # move to ldap3? - better docs

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

def checksession (sessioncode, people):
    """
    Validates a session code and retrieves a person document

    @sessioncode : The session code from the browser cookie

    @returns:      The document for the person associated with this session
    """

    person = people.find_one({"sessioncode":sessioncode})

    try:
        if "disabled" in person and person["disabled"]:
            raise Exception("Account disabled")
    except Exception as e:
        current_app.logger.exception(str(e))
        
    # if "disabled" in person and person["disabled"]:
    #     raise Exception("Account disabled")

    try:
        if person:
            return person
    except:
        current_app.logger.exception("Couldn't validate session")
    # Exception("Couldn't validate session")

def getnormaluser(people):
    form = get_form()
    person = checksession(form["session"], people)

    return person

def getadminuser(people):
    form = get_form()
    person = checksession(form["session"], people)

    if not person["is_admin"]:
        raise Exception("Not and admin")

    return person

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

def make_new_person(
    people,
    username: str,
    name: str = "",
    email: str = ""
):
    """
    :param people:
    :param username:
    :type username: str
    :param name:
    :type name: str
    :param email:
    :type email: str
    """
    if email == "":
        email = username + "@example.com"
    if name == "":
        name = username

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
    try:
        people.insert_one(new_person)
    except:
        current_app.logger.exception("Failed to create new person!")

def new_person_from_ldap(people, username, server_conf, conn):
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

    make_new_person(people, username, name, email)
