from functools import wraps
import flask
import time

#helper wrappers
def login_required():
    def wrapper(*args, **kwargs):
        if "credentials" not in flask.session:
            return flask.redirect("authorize")
        else:
            return "none"
    return wrapper()

def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}



def spliter(data: str):
    return data.split(".")[-1]

def ordinal(number):
    if 10 <= number % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')
    return str(number) + suffix



def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "credentials" not in flask.session:
            return flask.redirect("authorize")
        else:
            return f(*args, **kwargs)
    return decorated_function