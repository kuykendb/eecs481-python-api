from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from datetime import datetime

# We won't initialize the datastore yet, we'll let the 
# application do it. This allows multiple applications to
# share this models file.
db = SQLAlchemy()

# Define necessary relationary tables
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

skills_events = db.Table('skills_events',
    db.Column('skill_id', db.Integer(), db.ForeignKey('skill.id')),
    db.Column('event_id', db.Integer(), db.ForeignKey('event.id')))

events_users = db.Table('events_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('event_id', db.Integer(), db.ForeignKey('event.id')))

class Role(db.Model, RoleMixin):

    """Class to define user roles.

    Not currently utilized but could provide functionality for
    different types of users. Admins, volunteers, etc.
    """

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):

    """Class to represent a user"""

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(255))
    current_login_ip = db.Column(db.String(255))
    login_count = db.Column(db.Integer)
    roles = db.relationship('Role', secondary=roles_users, 
                            backref=db.backref('users', lazy='dynamic'))
    created_events = db.relationship('Event', backref='user', lazy='dynamic')
    attending_events = db.relationship('Event', secondary=events_users,
                                       backref='events', lazy='dynamic')
    current_hours = db.Column(db.Integer)
    goal_hours = db.Column(db.Integer)
    zipcode = db.Column(db.Integer)
    profile_pic_url = db.Column(db.String(255))
    lat = db.Column(db.Float(precision="20,17"))
    lon = db.Column(db.Float(precision="20,17"))

    # The following serializers allow us to return the user
    # object as JSON
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_events': self.serialize_created_events,
            'upcoming_events': self.serialize_upcoming_events,
            'recent_events': self.serialize_recent_events,
            'current_hours': self.current_hours,
            'goal_hours': self.goal_hours,
            'zipcode': self.zipcode,
            'profile_pic_url': self.profile_pic_url,
            'lat': self.lat,
            'lon': self.lon
       }

    @property
    def serialize_created_events(self):
        return [ event.serialize for event in self.created_events]

    @property
    def serialize_upcoming_events(self):
        upcoming = self.attending_events.filter(Event.end_date > datetime.now())  
        return [ event.serialize for event in upcoming]

    @property
    def serialize_recent_events(self):
        recent = self.attending_events.filter(Event.end_date < datetime.now())    
        return [event.serialize for event in recent]

class Event(db.Model):

    """Class to represent events

    This class is indexed by WhooshAlchemy and is 
    thus searchable.

    """

    # Define searchable fields to be indexed by WhooshAlchemy
    __tablename__ = 'event'
    __searchable__ = ['description', 'organization', 'name']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    short_desc = db.Column(db.String(255))
    organization = db.Column(db.String(255))
    description = db.Column(db.String(255))
    start_date = db.Column(db.DateTime())
    end_date = db.Column(db.DateTime())
    max_volunteers_needed = db.Column(db.Integer)
    current_num_volunteers = db.Column(db.Integer)
    close_date = db.Column(db.DateTime())
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_date = db.Column(db.DateTime())
    last_updated_date = db.Column(db.DateTime())
    pic_url = db.Column(db.String(255))
    street_addr = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    zipcode = db.Column(db.String(10))
    skills = db.relationship('Skill', secondary=skills_events,
                             backref=db.backref('skills', lazy='dynamic'))
    lat = db.Column(db.Float(precision="20,17"))
    lon = db.Column(db.Float(precision="20,17"))

    def __init__(self, name, short_desc, organization, description, start_date,
                 end_date, max_volunteers_needed, close_date, creator_id, 
                 street_addr, city, state, zipcode):

        self.name = name
        self.short_desc = short_desc
        self.description = description
        self.organization = organization
        self.start_date = start_date
        self.end_date = end_date
        self.max_volunteers_needed = max_volunteers_needed
        self.current_num_volunteers = 0
        self.close_date = close_date
        self.creator_id = creator_id
        self.street_addr = street_addr
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.created_date = datetime.now()
        self.last_updated_date = datetime.now()


    # The following serializers allow us to return the event
    # object as JSON
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id': self.id,
            'name': self.name,
            'short_desc': self.short_desc,
            'description': self.description,
            'organization': self.organization,
            'start_date': self.start_date.strftime("%m/%d/%Y"),
            'end_date': self.end_date.strftime("%m/%d/%Y"),
            'current_num_volunteers': self.current_num_volunteers,
            'max_volunteers_needed': self.max_volunteers_needed,
            'skills': self.serialize_skills,
            'close_date': self.close_date.strftime("%m/%d/%Y"),
            'creator_id': self.creator_id,
            'street_addr': self.street_addr,
            'city': self.city,
            'state': self.state,
            'zipcode': self.zipcode,
            'created_date': self.created_date.strftime("%m/%d/%Y"),
            'last_updated_date': self.last_updated_date.strftime("%m/%d/%Y"),
            'lat': self.lat,
            'lon': self.lon,
            'pic_url': self.pic_url
       }

    @property
    def serialize_skills(self):
       """
       Return object's relations in easily serializeable format.
       NB! Calls many2many's serialize property.
       """
       return [skill.name for skill in self.skills]

class Skill(db.Model):

    """Class to define a skill requested by an event."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

    def __init__(self, name):
        self.name=name

