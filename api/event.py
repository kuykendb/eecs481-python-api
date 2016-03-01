from datetime import datetime

from flask import *
from flask.ext.mysqldb import MySQL
from flask.ext.mysqldb import MySQLdb
from flask_restful import Resource, Api
from flask.ext.security.utils import encrypt_password, verify_password

from sqlalchemy.exc import IntegrityError
from werkzeug import secure_filename
import requests

from models.models import Event as db_event, Skill
from globals import *
from api import *

DEFAULT_EVENT_LIMIT = 10
"""Default limit for number of search results returned."""

MAX_SEARCH_RANGE = 6
"""Max range for location based search, in degrees.

Used to limit initial WooshAlchmey index based search 
to a roughly (2*MAX_SEARCH_RANGE)^2 sized box to optimize 
query time. 

NOTE: 6 degress is roughly 300 miles

"""

class EventList(Resource):

    """A class representing a list of events.

    This class provides the routes for creating
    events, and getting events based on text and
    location based searching.

    """

    def get(self):
        """Return list of events.

        URL parameters:
        - query: used to search for related events
        - zip: used to search for nearby events
        - raidus: used to limit range of nearby events
        - limit: used to limit number of events returned

        """

        # Grab all values from request URL
        query = request.values.get("query")
        zip = request.values.get("zip")
        radius = request.values.get("radius")
        limit = request.values.get("limit")

        # If limit cannot be cast as an int, 
        # fail gracefully and just use the default limit
        if limit is not None:
            try:
                limit = int(limit)
            except ValueError:
                limit = DEFAULT_EVENT_LIMIT

        # We only want to do location based search if
        # both a zipcode and a radius are provided
        use_location = False
        if zip is not None and radius is not None:

            try: 

                # Check if the zipcode and radius are integers
                zip = int(zip)
                radius = int(radius)

                # Grab the location based on zip
                location = get_location_from_zip(zip)

                # If we were able to fetch successfully fetch
                # coordinates, use the location for searching 
                if location is not None:
                    use_location = True
                else:
                    return get_error_response("Invalid zipcode.")

            except (ValueError, IndexError):

                # If location fetching failed, abandon search.
                return get_error_response("Invalid zipcode.")

        
        if query is None:
            # If no search query is provided, use all events
            results = db_event.query.all()

        else:
            if use_location == True:

                # This limits the inital query to a roughly (2*MAX_SEARCH_RANGE)^2  
                # mile box around the location and  prevents us from having 
                # to calculate the equirectangular distance for every event 
                # matching the query across the world.
                results = db_event.query.whoosh_search(query).filter(
                    db_event.lat < location["lat"] + MAX_SERACH_RANGE,
                    db_event.lat > location["lat"] - MAX_SEARCH_RANGE,
                    db_event.lon < location["lon"] + MAX_SEARCH_RANGE,
                    db_event.lon > location["lon"] - MAX_SEARCH_RANGE
                )

            else:
                results = db_event.query.whoosh_search(query)

        if use_location == True:

            # Now we further refine the search results by calculating
            # the actual equirectangular distance.
            for e in results:

                # Make sure the event's location is set
                if e.lat is not None and e.lon is not None: 

                    # Get distance between coordinates and convert to miles.
                    dist = calculate_equirectangular_distance(location["lat"], location["lon"],
                                                              e.lat, e.lon)
                    miles = 0.62 * dist

                    # Store the distance with each event for sorting later
                    e.dist = miles

            # Sort the results by distance
            results.sort(key=lambda event: event.dist)

        events = []

        # Each event must be serialized. Also, eliminate 
        # locations oustide radius if doing location based 
        # search and stop and return if we reach limit
        for e in results:

            if limit is not None and len(events)==limit:
                 return get_success_response({"events": events})
            
            if use_location and e.dist < radius:
                events.append(e.serialize)
            else:
                events.append(e.serialize)
        
        return get_success_response({"events": events})

    def post(self):
        """Create an event.

        Post body parameters:
        - event_name: name of the event
        - creator_id: user id of the creator
        - short_desc: short description of event for search results
        - full_desc: full description of event for event page
        - max_volunteers: maximum number of volunteers requested
        - close_date: date to stop accepting new volunteers
        - start_date: start date of the event
        - end_date: end date of the event
        - street_addr: street address
        - zipcode: zipcode - city and state found based on zip
        - organization: the organization putting on the event
        - skills: an array of desired skills for volunteers

        """

        app = current_app._get_current_object()
        db = app.db

        # Get POST body as JSON
        req_json = request.get_json()

        if req_json is not None:

            # Read all parameters and set necessary default values.
            event_name = req_json.get("event_name")
            creator_id = req_json.get("creator_id")
            zipcode = req_json.get("zipcode")
            start_date = req_json.get("start_date")
            max_volunteers = req_json.get("max_volunteers")

            if event_name is None or creator_id is None or zipcode is None \
               or start_date is None or max_volunteers is None:
                msg = "Missing required parameters."
                return get_error_response(msg)

            # It is not necessary to provided all details at creation time.
            short_desc = req_json.get("short_desc", None)
            full_desc = req_json.get("full_desc", None)
            street_addr = req_json.get("street_addr", None)
            organization = req_json.get("organization", None)
            skills = req_json.get("skills",[])

            # If not provided, set all default dates to current time. User can update later.
            close_date = req_json.get("close_date", datetime.now().strftime("%m/%d/%Y"))
            end_date = req_json.get("end_date", datetime.now().strftime("%m/%d/%Y"))

            # If the user provided a zipcode, set their coordinates
            zipcode = req_json.get("zipcode",None)
            if zipcode is not None:

                try: 

                    zip = int(zipcode)
                    location = get_location_from_zip(zip)       

                    # location will be None if zipcode is invalid
                    if location is None:
                        return get_error_response("Zipcode not found.")

                except (ValueError, IndexError):
                    return get_error_response("Zipcode not found.")


            if start_date is not None:
                start_date = datetime.strptime(start_date, '%m/%d/%Y')
            if end_date is not None:
                end_date = datetime.strptime(end_date, '%m/%d/%Y')
            if close_date is not None:
                close_date = datetime.strptime(close_date, '%m/%d/%Y')

            event = db_event(event_name,short_desc,organization,full_desc,start_date,end_date,max_volunteers,
                        close_date,creator_id,street_addr,location["city"],location["state"],zipcode)

            # Set latitude and longitude
            event.lat = location["lat"]
            event.lon = location["lon"]

            # Each event keeps a list of skills
            for s in skills:
                skill = Skill(s)
                event.skills.append(skill)

            try:

                # Push the event to the database
                db.session.add(event)
                db.session.commit()

            except IntegrityError:
                msg = "Foreign key error."
                return get_error_response(msg)

            return get_success_response({"event":event.serialize})

        else:

            msg = "Could not decode JSON from request."
            return get_error_response(msg)


class Event(Resource):

    """Class for fetching, updating and deleting events."""

    def get(self, event_id):
        """Return an event."""

        app = current_app._get_current_object()
        conn = app.mysql.connection
        cur = conn.cursor(MySQLdb.cursors.DictCursor)

        e = db_event.query.filter_by(id=str(event_id)).first()

        return get_success_response({"event": e.serialize})

    def post(self, event_id):
        """Update an event.

        Post body parameters:
        - event_name: the name of the event
        - creator_id: id of the user who created the event
        - short_desc: short description to display with search results
        - full_desc: full event description for event page
        - start_date: start date of the event
        - end_date: end date of the event
        - max_volunteers: maximum number of volunteers requested for event
        - close_date: date to stop accepting new volunteers
        - street_addr
        - city
        - state
        - zipcode

        """
        
        app = current_app._get_current_object()
        db = app.db

        # get POST body as JSON
        req_json = request.get_json()

        # All params have a default of None. We will
        # only update params that are not None
        event_name = req_json.get("event_name", None)
        short_desc = req_json.get("short_desc", None)
        full_desc = req_json.get("full_desc", None)
        max_volunteers = req_json.get("max_volunteers", None)
        close_date = req_json.get("close_date", None)
        start_date = req_json.get("start_date", None)
        end_date = req_json.get("end_date", None)
        street_addr = req_json.get("street_addr", None)
        zipcode = req_json.get("zipcode", None)
        organization = req_json.get("organization", None)
        skills = req_json.get("skills",[])

        # If the user provided a zipcode, set their coordinates
        zipcode = req_json.get("zipcode",None)
        if zipcode is not None:

            try: 

                zip = int(zipcode)
                location = get_location_from_zip(zip)       

                # location will be None if zipcode is invalid
                if location is None:
                    return get_error_response("Zipcode not found.")

            except (ValueError, IndexError):
                return get_error_response("Zipcode not found.")

        if start_date is not None:
            start_date = datetime.strptime(start_date, '%m/%d/%Y')
        if end_date is not None:
            end_date = datetime.strptime(end_date, '%m/%d/%Y')
        if close_date is not None:
            close_date = datetime.strptime(close_date, '%m/%d/%Y')

        event = db_event.query.filter_by(id=str(event_id)).first()

        if event is not None:

            # Only update params that were given.
            event.name = event_name or event.name
            event.short_desc = short_desc or event.short_desc
            event.description = full_desc or event.description
            event.start_date = start_date or event.start_date
            event.end_date = end_date or event.end_date
            event.max_volunteers_needed = max_volunteers or event.max_volunteers_needed
            event.close_date = close_date or event.close_date
            event.street_addr = street_addr or event.street_addr
            event.zipcode = zipcode or event.zipcode
            event.organization = organization or event.organization

            if location is not None:
                event.city = location["city"] or event.city
                event.state = location["state"] or event.state
                event.lat = location["lat"] or event.lat
                event.lon = location["lon"] or event.lon

            # Current skills array is always passed, so we
            # can just replace the entire array
            event.skills = []
            for s in skills:
                skill = Skill(s)
                event.skills.append(skill)

            db.session.commit()

            return get_success_response({"event": event.serialize})

        else:
            return get_error_response("Event not found.")


    def delete(self, event_id):
        """Delete an event."""

        app = current_app._get_current_object()
        conn = app.mysql.connection
        cur = conn.cursor(MySQLdb.cursors.DictCursor)

        cur.execute("DELETE FROM event WHERE id=%s",({event_id}))
        conn.commit()

        return get_success_response()


class EventPic(Resource):

    """Class to handle update picture route."""

    def post(self,event_id):
        """Update the picture for an event.

        Stores the picture in the server filesystem and
        updates event's pic_url. Would be good in the future
        to use Amazon S3 storage for images.
        """

        app = current_app._get_current_object()

        file = request.files['file-0']
        if file:

            # Save the pic to filesystem
            filename = secure_filename(event_id + "_" + datetime.now().strftime("%Y%m%d%H%M%S"))
            file.save(os.path.join(app.config['EVENT_PIC_UPLOAD_FOLDER'], filename))

            # Save pic url to user
            db = app.db

            event = db_event.query.filter_by(id=str(event_id)).first()

            if event is not None:

                # delete the old pic if there was one
                if event.pic_url is not None:
                    os.remove(os.path.join(app.config['EVENT_PIC_UPLOAD_FOLDER'], event.pic_url))

                event.pic_url = filename

                db.session.commit()

                return get_success_response({"filename": filename})

            return get_error_response("Event not found.")

        return get_error_repsonse("No file provided.")
