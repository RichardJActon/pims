# login
from flask import Blueprint, render_template, make_response, current_app, redirect, url_for
from pims.session import *
from pims.utility import jsonify

import time
import ldap # move to ldap3? - better docs # move to ldap3? - better docs

def construct_bp(people, projects, ips):
    
    bp = Blueprint('login', __name__) 
    @bp.route("/login")
    def login():
        return render_template("pages/login.html")

    @bp.route("/processlogin", methods = ['POST', 'GET'])
    def process_login():
        """
        Validates an username / password combination and generates
        a session id to authenticate them in future

        :param username: Their BI username
        :param password: The unhashed version of their password

        :return: Forwards the session code to the json response
        """
        form = get_form()
        username = form["username"]
        password = form["password"]

        testing_no_auth = True
        if testing_no_auth:
            
            sessioncode = generate_id(20)
            response = make_response(sessioncode)
            response.set_cookie("pims_session_id",sessioncode)
            
            person = people.find_one({"username":username})
            if not person:
                current_app.logger.info("NOT PERSON - MAKING NEW!")
                # print("NOT PERSON - MAKING NEW!")
                # Now we can make the database entry for them
                # creating new DB entries for unauthenticated users is a
                # potential DOS vector, rate limit?
                # clean old entries with no sucessfull logins? - time since last failed login
                make_new_person(people, username)
                # name  = username
                # email = username + "@example.com"

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
                    new_person_from_ldap(people, username, server_conf, conn)
                    # # We're making a new person.  We can therefore query AD
                    # # to get their proper name and email.

                    # # We can theoretically look anyone up, but this filter says
                    # # that we're only interested in the person who logged in
                    # filter = f"(&(sAMAccountName={username}))"

                    # # The values we want to retrive are their real name (not 
                    # # split by first and last) and their email
                    # search_attribute = ["distinguishedName","mail"]

                    # # This does the search and gives us back a search ID (number)
                    # # which we can then use to fetch the result data structure
                    # dc_string = ",".join(["DC="+x for x in server_conf["server"]["ldap"].split(".")])
                    # res = conn.search(dc_string,ldap.SCOPE_SUBTREE, filter, search_attribute)
                    # answer = conn.result(res,0)

                    # # We can then pull the relevant fields from the results
                    # name = answer[1][0][1]["distinguishedName"][0].decode("utf8").split(",")[0].replace("CN=","")
                    # email = answer[1][0][1]["mail"][0].decode("utf8")

                    # make_new_person(people, username, name, email)

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

    # bp = Blueprint('logout', __name__)
    # @bp.route("/logout")
    # def logout():
    #     # session.pop("user_id", None)
    #     return redirect(url_for("pages.login"))

    @bp.route("/validate_session", methods = ['POST', 'GET'])
    def validate_session():
        form = get_form()
        person = checksession(form["session"], people)
        return(str(person["name"]))

    @bp.route("/get_user_data", methods = ['POST', 'GET'])
    def get_user_data():
        form = get_form()
        person = checksession(form["session"], people)
        return jsonify(person)

    return bp

