# auth
from flask import (
    session,
    url_for,
    redirect,
)
from functools import wraps
from typing import (
    Dict,
    Any,
)
from authlib.integrations.flask_client import OAuth

def register_oauth_endpoints(oauth: OAuth, endpoints: Dict[str, Any]) -> None:
    """
    Note that the `openid` scope is expected to be requested and the useinfo
    within it is expected to be present in the token.
    """
    for k,v in endpoints.items():
        oauth.register(k, **v)

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("user") is None:
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)
    return decorated

