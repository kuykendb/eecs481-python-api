import os

UPLOAD_FOLDER = "static/images/profile_pics"
EVENT_PIC_UPLOAD_FOLDER = "static/images/event_pics"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
GMAPS_API_KEY = "your-key-goes-here"

if os.environ.get("SERVER_SOFTWARE") is None:
	#
	# Your browser will probably complain about cross domain origin issues
	# if you leave API_SERVER pointed to the live API while trying 
	# to run this locally. Also, it will probably complain if 
	# the API is not running on the same domain as the website. What I did
	# was add the following two entries to /etc/hosts:
	#
	# 127.0.0.2       volunteering.app
	# 127.0.0.3       api.volunteering.app
	#
	# You'll probably also have to run these two commands to make 127.0.0.2/3
	# available as local loopback addresses:
	#
	# sudo ifconfig lo0 alias 127.0.0.2 up
	# sudo ifconfig lo0 alias 127.0.0.3 up
	# 
	# Then things should work and you should be able to acces the website at:
	# 
	#		http://volunteering.app:5000/
	#
	# and the API at:
	#
	#		http://api.volunteering.app:5000/
	#
	# Web dev is kind of a pain in the ass haha.
	#
	#
	API_SERVER = "http://0.0.0.0:8889"
else:
	# SEVER_SOFTWARE = Google App Engine/X.Y.Z when LIVE, so this will be 
	# use when the app is deployed
	API_SERVER = "http://api.eecs481volunteering1.appspot.com"