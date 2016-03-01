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

from api.event import EventList,Event, EventPic
from api.volunteer import VolunteerList,Volunteer,EventsVolunteers, \
    ProfilePic, Login
from models.models import User, Role, Event as dbEvent, RoleMixin, db
from globals import *

class CustomJSONEncoder(JSONEncoder):

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

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

# woosh-alchemy
app.config['WHOOSH_BASE'] = 'index'
flask.ext.whooshalchemy.whoosh_index(app,dbEvent)

app.config['MYSQL_HOST']="localhost"
app.config['MYSQL_USER']="root"
app.config['MYSQL_DB']="volunteer_app"

# init MySQL
app.mysql = MySQL(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root@localhost:3306/volunteer_app"

# Configure Flask-Security
app.config["SECURITY_REGISTERABLE"] = True
app.config["SECURITY_CONFIRMABLE"] = False
app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'

# pbkdf2_sha512 generates its own salt. We still need
# to provide this line to prevent a bug from happening
app.config['SECURITY_PASSWORD_SALT'] = 'xxxxxxxxxxxx' 

app.config['SECRET_KEY'] = 'FmG9yqMxVfb9aoEVpn6J'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EVENT_PIC_UPLOAD_FOLDER'] = EVENT_PIC_UPLOAD_FOLDER

# Instatiate the database connection object
db.init_app(app)
app.db = db

# Initialize Flask-Security and SQLAlchemy datastore
# so we can create users
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Initialize the Api
api = Api(app)

api.add_resource(Login,'/user/loginUser')

api.add_resource(EventList, '/events')
api.add_resource(Event, '/event/<event_id>')
api.add_resource(VolunteerList,'/users')
api.add_resource(Volunteer,'/user/<user_id>')
api.add_resource(EventsVolunteers,'/event/<event_id>/<user_id>')

api.add_resource(ProfilePic,'/user/<user_id>/picture')
api.add_resource(EventPic,'/event/<event_id>/picture')

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8889,debug=True)
