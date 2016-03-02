from math import cos, sqrt, radians

from flask import *
from flask.ext.mysqldb import MySQL
from flask.ext.mysqldb import MySQLdb

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
