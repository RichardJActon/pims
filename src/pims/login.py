# Login ----
from flask import (
    Blueprint,
    render_template,
    make_response,
    current_app,
    redirect,
    url_for,
    session,
)

from pims.session import *
from pims.utility import jsonify

from datetime import datetime
import time
import ldap # move to ldap3? - better docs # move to ldap3? - better docs

def construct_bp(people, projects, ips, oauth, oauth_providers):
    bp = Blueprint('login', __name__) 
    
    @bp.route('/login')
    def login():
        return render_template("pages/login.html", oauth_providers = oauth_providers)

    @bp.route('/oauth_login/<oauth_provider>')
    def oauth_login(oauth_provider):
        redirect_uri = url_for('login.authorize', oauth_provider = oauth_provider, _external=True)
        return oauth.__getattr__(oauth_provider).authorize_redirect(redirect_uri)

    @bp.route('/authorize/<oauth_provider>')
    def authorize(oauth_provider):
        token = oauth.__getattr__(oauth_provider).authorize_access_token()
        userinfo = token.get('userinfo')
        current_app.logger.info(
            "User: " + userinfo.get('preferred_username') +
            " logged in, Authorised at: " +
            str(datetime.fromtimestamp(userinfo.get('auth_time')))
        )
        # resp = oauth.testing.get('user')
        # resp.raise_for_status()
        # profile = resp.json()
        user_query = {"username": userinfo["preferred_username"]}
        person = people.find_one(user_query)
        try:
            if person is None:
                make_new_person(
                    people,
                    username = userinfo['preferred_username'],
                    name = userinfo['given_name'] + ' ' + userinfo['family_name'],
                    email = userinfo['email']
                )
                person = people.find_one(user_query)
                raise Exception(
                    f"Person not found in database, created new Person: {userinfo['preferred_username']}"
                )
        except Exception as e:
            current_app.logger.info(e)

        try:
            if "disabled" in person and person["disabled"]:
                raise Exception(f"Account disabled for {person['username']}!")
            else:
                session["user"] = userinfo
                session["id_token"] = token.get("id_token")
                session["oauth_provider"] = oauth_provider
        except Exception as e:
            current_app.logger.info(str(e))
        
        # session["user"] = oauth.testing.userinfo()
        # current_app.logger.info(session.get('user').get('userinfo'))
        return redirect('/')
        # return redirect('/profile')

    # debugging user info
    # @bp.route("/profile")
    # def profile():
    #     userinfo = session.get("user")
    #     return f"<p>{str(userinfo)}</p>"

    @bp.route("/logout")
    def logout():
        id_token = session.pop("id_token", None)
        redirect_uri = url_for('login.logged_out', _external=True)
        return oauth.__getattr__(session.get("oauth_provider")).logout_redirect(
            post_logout_redirect_uri = redirect_uri,
            id_token_hint = id_token
        )

    @bp.route('/logged_out')
    def logged_out():
        state_data = oauth.__getattr__(session["oauth_provider"]).validate_logout_response()
        # state_data just contains the re-direct URL to this page
        session.pop("user", None)
        return render_template("pages/logout_confirmation.html")

    # @bp.route("/processlogin", methods = ['POST', 'GET'])
    # def process_login():
    #     """
    #     Validates an username / password combination and generates
    #     a session id to authenticate them in future

    #     :param username: Their BI username
    #     :param password: The unhashed version of their password

    #     :return: Forwards the session code to the json response
    #     """
    #     form = get_form()
    #     username = form["username"]
    #     password = form["password"]

    #     testing_no_auth = True
    #     if testing_no_auth:
            
    #         sessioncode = generate_id(20)
    #         response = make_response(sessioncode)
    #         response.set_cookie("pims_session_id",sessioncode)
            
    #         person = people.find_one({"username":username})
    #         if not person:
    #             current_app.logger.info("NOT PERSON - MAKING NEW!")
    #             # print("NOT PERSON - MAKING NEW!")
    #             # Now we can make the database entry for them
    #             # creating new DB entries for unauthenticated users is a
    #             # potential DOS vector, rate limit?
    #             # clean old entries with no sucessfull logins? - time since last failed login
    #             make_new_person(people, username)
    #             # name  = username
    #             # email = username + "@example.com"

    #         people.update_one({"username":username},{"$set":{"sessioncode": sessioncode}})
    #         return(response)
    #     else: 
    #         ip_lockout(
    #             people, username, ips,
    #             server_conf["security"]["lockout_time_mins"],
    #             server_conf["security"]["failed_logins_per_ip"]
    #         )
            

    #         # Check the password against AD
    #         conn = ldap.initialize("ldap://"+server_conf["server"]["ldap"])
    #         conn.set_option(ldap.OPT_REFERRALS, 0)

    #         # bypass auth
    #         response = make_response(sessioncode)
    #         response.set_cookie("pims_session_id",sessioncode)
    #         return(response)

    #         try:    
    #             conn.simple_bind_s(username+"@"+server_conf["server"]["ldap"], password)

    #             # Clear any IP recorded login fails
    #             ips.delete_one({"ip":request.remote_addr})

    #             sessioncode = generate_id(20)

    #             if not person:
    #                 new_person_from_ldap(people, username, server_conf, conn)

    #             people.update_one({"username":username},{"$set":{"sessioncode": sessioncode}})

    #             response = make_response(sessioncode)
    #             response.set_cookie("pims_session_id",sessioncode)
    #             return(response)
    
    #         except ldap.INVALID_CREDENTIALS:
    #             # We need to record this failure.  If there is a user with this name we record
    #             # against that.  If not then we just record against the IP
    #             if person:
    #                 people.update_one({"username":username},{"$push":{"failed_logins":int(time.time())}})
    #                 if len(person["failed_logins"])+1 >= server_conf["security"]["failed_logins_per_user"]:
    #                     # We need to lock their account
    #                     people.update_one({"username":username},{"$set":{"locked_at":int(time.time())}})
                

    #         if not ip:
    #             ips.insert_one({"ip":request.remote_addr,"failed_logins":[]})

    #         ips.update_one({"ip":request.remote_addr},{"$push":{"failed_logins":int(time.time())}})

    #         raise Exception("Incorrect Username/Password from LDAP")

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

