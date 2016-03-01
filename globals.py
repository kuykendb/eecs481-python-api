import os

UPLOAD_FOLDER = "static/images/profile_pics"
EVENT_PIC_UPLOAD_FOLDER = "static/images/event_pics"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# If server software environment variable is not set,
# then we currently running on localhost
if os.environ.get("SERVER_SOFTWARE") is None:
	API_SERVER = "http://0.0.0.0:8889"
else:
	API_SERVER = "http://api.eecs481volunteering1.appspot.com"