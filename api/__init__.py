from math import cos, sqrt, radians
from functools import wraps

from flask import *
from flask.ext.mysqldb import MySQL
from flask.ext.mysqldb import MySQLdb

from itsdangerous import (TimedJSONWebSignatureSerializer
    as Serializer, BadSignature, SignatureExpired)

from models.models import User as db_user
from globals import *

def key_required(f):
    """Decorator to require API KEY for every request.

    The API KEY must be present in the request as a header
    with a key "api_key".
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        app = current_app._get_current_object()
        key = request.headers.get("api_key")

        if key == API_KEY:
            return f(*args, **kwargs)
        else:
            return get_error_response("Unauthorized.")
    return decorated_function

def auth_required(f):
    """Decorator to require a valid token.

    Token must be present in authorization header.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        app = current_app._get_current_object()
        token = request.headers.get("authorization")

        if verify_auth_token(app, token):
            return f(*args, **kwargs)
        else:
            return get_error_response("Unauthorized.")
    return decorated_function

def verify_auth_token(app, token):
    """Verify that the presented token is valid."""

    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return False # valid token, but expired
    except BadSignature:
        return False # invalid token
    return True

def calculate_equirectangular_distance(lat1, lon1, lat2, lon2):
    """Calculate the equirectangular distance between two coordinates."""

    lon1 = radians(float(lon1))
    lon2 = radians(float(lon2))
    lat1 = radians(float(lat1))
    lat2 = radians(float(lat2))

    earth_radius = 6371
    x = (lon2 - lon1) * cos(0.5 * (lat2 + lat1))
    y = lat2 - lat1
    dist = (earth_radius * sqrt((x * x) + (y * y)))

    return dist

def get_location_from_zip(zipcode):
    """Get coordinates for the provided zipcode.

    Returns None if no coordinates were found that
    match the zipcode.

    """

    app = current_app._get_current_object()
    conn = app.mysql.connection
    cur = conn.cursor(MySQLdb.cursors.DictCursor)

    cur.execute("SELECT lat, lon, city, state FROM location WHERE \
                zipcode='%s' GROUP BY zipcode;", ({zipcode}))

    result = cur.fetchone()

    return result

def get_success_response(results = {}):
    """Format the success JSON response object """

    results["success"] = True
    return jsonify(results)

def get_error_response(message):
    """Format the error JSON response object """

    response = jsonify({
        "success": False,
        "error": message
    })
    return response
