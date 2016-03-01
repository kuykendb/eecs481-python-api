#EECS 481 Fall 2015
##Volunteerism Crowdsourcing Application

This repository contains the backend and website for our web application to crowdsource volunteerism. The goal of the project is to provide a web application through which volunteer organizations can crowdsource their service needs. At a high level, the application consists of an iOS application which interfaces with a JSON web API.

## Backend Architecture

The backend consists of a Python Flask web API receiving and responding to JSON requests.

The API application is defined in api.py and with components defined in the api package.

The application runs on the Gunicorn WSGI server. Nginx is used as a reverse proxy server to forward requests to the correct Python process. The entire stack is running on an AWS Linux server and interfaces with an Amazon RDS MySQL database server.