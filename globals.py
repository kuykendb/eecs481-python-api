import os

API_KEY = "1305a38c9c2932f979e0dfb2d8d110f070e382d9750f19280d96394b51ac9c2d"

UPLOAD_FOLDER = "static/images/profile_pics"
EVENT_PIC_UPLOAD_FOLDER = "static/images/event_pics"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# If server software environment variable is not set,
# then we currently running on localhost
if os.environ.get("SERVER_SOFTWARE") is None:
    API_SERVER = "http://0.0.0.0:8889"
else:
    API_SERVER = "http://api.eecs481volunteering1.appspot.com"