from flask import request

def args_to_dict(args):
    form = {}

    for key in args.keys():
        if key.endswith("[]"):
            form[key[:-2]] = args.getlist(key)
        else:
            form[key] = args.get(key)

    return form

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

    if "disabled" in person and person["disabled"]:
        raise Exception("Account disabled")

    if person:
        return person

    raise Exception("Couldn't validate session")

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

