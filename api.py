import hashlib
import os
from os import urandom
from base64 import b64encode, b64decode
from datetime import datetime
from pbkdf2 import crypt
from passlib.hash import pbkdf2_sha512
import calendar

from flask import *
from flask.ext.mysqldb import MySQL
from flask.ext.mysqldb import MySQLdb
from flask_restful import Resource, Api
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, utils
from flask.json import JSONEncoder
import flask.ext.whooshalchemy

from api.event import EventList, Event, EventPic
from api.user import UserList, User, EventsUsers, \
    ProfilePic, Login
from models.models import User as db_user, Event as db_event, \
    Role, RoleMixin, db
from globals import *

class CustomJSONEncoder(JSONEncoder):

    """Custom JSON encoder to handle datetime objects."""

    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.strftime("%Y/%m/%d")
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)

# Initialize the main Flask application
app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

# WooshAlchemy Configuration
app.config['WHOOSH_BASE'] = 'index'
flask.ext.whooshalchemy.whoosh_index(app, db_event)

# MySQL Configuration
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_DB'] = "volunteer_app"
app.mysql = MySQL(app)

# SQLAlchemy Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root@localhost:3306/volunteer_app"

# Flask-Security Configuration
app.config["SECURITY_REGISTERABLE"] = True
app.config["SECURITY_CONFIRMABLE"] = False
app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'

# pbkdf2_sha512 generates its own salt. We still need
# to provide this line to prevent a bug from happening
app.config['SECURITY_PASSWORD_SALT'] = 'xxxxxxxxxxxx' 
app.config['SECRET_KEY'] = 'FmG9yqMxVfb9aoEVpn6J'

# General Application Configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EVENT_PIC_UPLOAD_FOLDER'] = EVENT_PIC_UPLOAD_FOLDER

# Instatiate the database connection object defined
# in the models file.
db.init_app(app)
app.db = db

# Initialize Flask-Security and SQLAlchemy datastore
user_datastore = SQLAlchemyUserDatastore(db, db_user, Role)
security = Security(app, user_datastore)

# Initialize the Flask-Restful API object
api = Api(app)

# Add routes for users defined in api/user.py
api.add_resource(Login, '/user/loginUser')
api.add_resource(UserList ,'/users')
api.add_resource(User, '/user/<user_id>')
api.add_resource(ProfilePic, '/user/<user_id>/picture')
api.add_resource(EventPic, '/event/<event_id>/picture')

# Add routes for events defined in api/events.py
api.add_resource(EventsUsers, '/event/<event_id>/<user_id>')
api.add_resource(EventList, '/events')
api.add_resource(Event, '/event/<event_id>')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8889, debug=True)
