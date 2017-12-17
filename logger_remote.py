#!/usr/bin/env python
# Python 3.6.3
# logger_remote.py

"""
logger_remote.py:
Client library POSTs url-encoded messages containing error level, facility name, and error message to logger_httpd.py.
User defined name value pairs can be logged in addition to the level, facility and message.
Logging to the remote server is supported using a standard Python library logging.handlers.HTTPHandler.
Run python logger_remote.py to generate a stream of random test messages.
Authentication can be by basic auth over SSL.

Usage:
import logger_remote
logger = logger_remote.get_logger(__name__)
record = { 'key': 'value' }
logger.log(level, 'error message', extra=record)
logger_remote.shutdown()

POST equivalent:
curl -i -d 'name=facility_name' -d 'levelno=40' -d 'msg=error message' -d 'additional_key=additional_value' http://localhost:8080/api/v1/messages

TODO: Add SSL and basic auth. Read userid/password from a file or the environment.
TODO: Inspect internal operation of logging.handlers.HTTPHandler in case of client side errors that need to be caught.
TODO: Catch remote logging server down exception.
TODO: Consider reporting server responses in general in case of error.
"""

import logging, logging.handlers
import datetime
import sys
import os
import random

host = 'localhost:8080'
route = '/api/v1/messages'

def get_logger(facility):
    """
    Return logger object used to send messages to remote logging server.
    This call only wraps four lines of logging library calls to set up a logger in a single call.
    """
    logger = logging.getLogger(facility) # Set up standard library logger named with the facility name.
    http_handler = logging.handlers.HTTPHandler(host, route, method='POST') # secure=True, context=ssl.SSLContext, credentials=(userid, password)
    # http_handler.setLevel(logging.INFO) # Level defaults to INFO, DEBUG or 0 will not be sent.
    http_handler.raiseExceptions = False # Suppress exceptions in use.
    logger.addHandler(http_handler) # Log everything through this handler without filtering.
    return logger # Pass back the logger object.

def shutdown():
    """
    Orderly shutdown for application exit.
    """
    return logging.shutdown()

# Generate random test messages and send to remote logging server.
if __name__ == '__main__':

    # Prepare 3 test loggers with different facility names to generate messages.
    loggers = list(get_logger(facility) for facility in ('facility_one', 'facility_two', 'facility_three')) # Generate 3 test loggers.
    message_limit = 1000 # Log a number of test messages and then quit.
    try:
        messages = ['Something went wrong message.', 'Houston has a problem message.', 'Something else in the red message.']
        while message_limit:
            message_limit -= 1 # Decrement message count.
            logger = loggers[random.randrange(3)] # Pick a random facility.
            levelno = (20, 25, 30, 40, 50, 60, 70)[random.randrange(7)] # Pick a random log level (logging.CRITICAL etc).
            message = messages[random.randrange(3)] # Pick a slightly random message.
            record = {'key':'value', 'an':'other'} # Add additional data to demonstrate.
            logger.log(levelno, message, extra=record) # Send to logging server.

    except KeyboardInterrupt:
        pass

    shutdown() # Orderly application exit.

