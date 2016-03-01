import os
from datetime import datetime
import json

from flask import *
from flask.ext.mysqldb import MySQL
from flask.ext.mysqldb import MySQLdb
from flask_restful import Resource, Api
from flask.ext.security import utils

from sqlalchemy.exc import IntegrityError
from models.models import Event as db_event, User as db_user
from werkzeug import secure_filename
from geopy.geocoders import Nominatim

from globals import *
import requests
from api import *

def allowed_file(filename):
	"""Check if the file type is allowed."""

	return '.' in filename and \
	       filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

class Login(Resource):

	"""Class to handle user login route"""

	def post(self):
		"""Log user in.

		"""

		req_json = request.get_json()

		email = req_json["email"]
		password = req_json["password"]

		user = db_user.query.filter_by(email=str(email)).first()

		if user is not None:
			if utils.verify_password(password,user.password):
				return json.jsonify(user=user.serialize)
			else:
				return json.jsonify(error="Invalid password!")
		else:
			return json.jsonify(error="User does not exist!")

class ProfilePic(Resource):

	"""Class to handle profile pic routes."""

	def post(self,user_id):
		"""Update profile picture"""

		app = current_app._get_current_object()

		file = request.files['file-0']
		if file:

			# Save the pic to filesystem
			filename = secure_filename(user_id + "_" + datetime.now().strftime("%Y%m%d%H%M%S"))
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

			# Updated user's pic url
			db = app.db

			user = db_user.query.filter_by(id=str(user_id)).first()

			# Make sure to delete the old pic if there was one
			if user.profile_pic_url is not None:
				os.remove(os.path.join(app.config['UPLOAD_FOLDER'], user.profile_pic_url))

			user.profile_pic_url = filename

			db.session.commit()

			result = {
				"filename":filename
			}

			return get_success_response(result)

		return get_error_response("Upload error.")


class UserList(Resource):

	"""Class to handle user creation routes."""

	def post(self):
		"""Create a new user."""

		app = current_app._get_current_object()
		db = app.db

		req_json = request.get_json()

		user = db_user()

		# Email is required
		user.email = req_json.get("email",None)
		if user.email is None:
			msg = "Must provide email!"
			return get_error_response(msg)

		# Name can be specified later
		user.first_name = req_json.get("first_name",None)
		user.last_name = req_json.get("last_name",None)

		password = req_json.get("password",None)
		confirm = req_json.get("confirmation",None)

		# Password and confirmation are required
		if password is None or confirm is None:
			msg = "Must provide password and confirmation!"
			return get_error_response(msg)

		if password != confirm:
			msg = "Password and confirmation do not match!"
			return get_error_response(msg)

		user.password = utils.encrypt_password(password)
		user.active = 1

		# If the user provided a zipcode, set their coordinates
		zipcode = req_json.get("zipcode",None)
		if zipcode is not None:

			try: 

				zip = int(zipcode)
				coordinates = get_location_from_zip(zip)		

				# coorindates will be None if no coordinates
				# were found that match the provided zipcode
				if coordinates is not None:	

					user.lat = coordinates["lat"]
					user.lon = coordinates["lon"]
					user.zipcode = zipcode

			except (ValueError, IndexError):
				user.zipcode = None

		try:
			# Save the user
			db.session.add(user)
			db.session.commit()

		except IntegrityError:
			msg = "Foreign key error."
			return get_error_response(msg)

		result = {
			"user": user.serialize
		}

		return get_success_response(result)


class User(Resource):

	"""Class to handle fetching, updating and deleting users."""

	def get(self,user_id):
		"""Return user."""

		u = db_user.query.filter_by(id=str(user_id)).first()

		if u is not None:
			return get_success_response({"user": u.serialize})

		return get_error_response("User not found.")

	def post(self, user_id):
		"""Update user."""

		app = current_app._get_current_object()
		db = app.db

		req_json = request.get_json()

		user = db_user.query.filter_by(id=str(user_id)).first()

		# Make sure the user exists
		if user is not None:

			# If request body was provided, there is nothing
			# to update
			if len(req_json) <= 0:
				result = {"user": user.serialize}
				return get_success_response(result)

			# We only want to update fields that the user 
			# requested to update. If any field is None,
			# then don't update it
			email = req_json.get("email", None)
			if email is not None and len(email) > 0:
				user.email = email

			first_name = req_json.get("first_name" ,None)
			if first_name is not None and len(first_name) > 0:
				user.first_name = first_name

			last_name = req_json.get("last_name", None)
			if last_name is not None and len(last_name) > 0:
				user.last_name = last_name

			# Check if the user is changing their password
			password = req_json.get("password",None)
			confirm = req_json.get("confirm",None)

			if password is not None and confirm is not None:
				if password != confirm:
					msg = "Password and confirmation do not match!"
					return get_error_response(msg)
				else:
					user.password = utils.encrypt_password(password)

			current_hours = req_json.get("current_hours",None)
			goal_hours = req_json.get("goal_hours",None)

			try:

				if current_hours is not None:
					user.current_hours = int(current_hours)

			except ValueError:
				# If the value provided can't be converted to an int,
				# move on and don't update the value.
				pass

			try:

				if goal_hours is not None:
					user.goal_hours = int(goal_hours)

			except ValueError:
				pass

			# Update user location
			zipcode = req_json.get("zipcode",None)
			if zipcode is not None:

				try: 

					zip = int(zipcode)
					coordinates = get_location_from_zip(zip)		

					# coorindates will be None if no coordinates
					# were found that match the provided zipcode
					if coordinates is not None:	

						user.lat = coordinates["lat"]
						user.lon = coordinates["lon"]
						user.zipcode = zipcode

				except (ValueError, IndexError):
					zipcode = None

			db.session.commit()

			# Return the updated user
			result = {"user": user.serialize}
			return get_success_response(result)

		else:
			return get_error_response("User does not exist!")

	def delete(self, user_id):
		"""Delete user."""

		app = current_app._get_current_object()
		db = app.db

		user = db_user.query.filter_by(id=str(user_id)).first()

		if user is None:
			return get_error_response("User not found.")

		db.session.delete(user)
		db.session.commit()

		return get_success_response()


class EventsUsers(Resource):

	"""Class for adding and removing users to events."""

	def get(self, user_id):
		"""Get user's events."""

		return get_success_response()

	def post(self, event_id, user_id):
		"""Add user to event."""

		app = current_app._get_current_object()
		conn = app.mysql.connection
		cur = conn.cursor(MySQLdb.cursors.DictCursor)

		cur.execute("INSERT INTO events_users (event_id,user_id) VALUES (%s,%s)",({event_id},{user_id}))
		cur.execute("UPDATE event SET current_num_volunteers=current_num_volunteers+1 WHERE id=%s",({event_id}))

		conn.commit()

		return get_success_response()

	def delete(self, event_id, user_id):
		"""Remove user from event."""

		app = current_app._get_current_object()
		conn = app.mysql.connection
		cur = conn.cursor(MySQLdb.cursors.DictCursor)

		cur.execute("DELETE FROM events_users WHERE event_id=%s and user_id=%s",({event_id},{user_id}))
		cur.execute("UPDATE event SET current_num_volunteers=current_num_volunteers-1 WHERE id=%s",({event_id}))

		conn.commit()

		return get_success_response()
