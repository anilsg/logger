#!/usr/bin/env python
# Python 3.6.3
# curl -i -d 'facility=facility_name' -d 'level=40' -d 'message=error_name' -d 'datestamp=20171203-123456.123456' -d 'additional_key=additional_value' http://localhost:8080/api/v1/messages

"""
Remote logging client: remote_logger.py

Logging to the remote logging server is supported by a standard library HTTP logger.
remote_logger just wraps the four lines to set one up in a single call.
Extra name value pairs for logging in addition to the message can be supplied in dict record.
Usage:
    import remote_logger
    logger = remote_logger.getLogger(__name__)
    logger.log(level, 'new_message', extra=record)
    remote_logger.shutdown()

remote_logger passes log message and values to the remote server in a url encoded POST
to the pre-configured conventional remote logging server address, using SSL and basic auth (TODO).
Run this file to start a continuous stream of random test logging messages.

Example of some of the values passed:
    created=1512386686.0873692
    name=test_facility
    levelno=50
    levelname=CRITICAL
    msg=Something went wrong message.

TODO: Add SSL support and basic auth. Can read userid/password from a file, if don't want to hard code.
TODO: Catch server down exception.
"""

import logging, logging.handlers
import datetime
import sys
import os
import random

host = 'localhost:8080'
route = '/api/v1/messages'

def getLogger(facility):
    """
    Return logger object used to send messages to remote logging server and to shutdown the logger.
    """
    logger = logging.getLogger(facility) # Standard library logger.
    http_handler = logging.handlers.HTTPHandler(host, route, method='POST') # secure=True, context=ssl.SSLContext, credentials=(userid, password)
    http_handler.setLevel(logging.INFO) # Using logging.DEBUG or 0 may raise the rate of message passing too high.
    http_handler.raiseExceptions = False # Suppress exceptions in use.
    logger.addHandler(http_handler) # Log everything through this handler without filtering.
    return logger # Pass back the logger object.

def shutdown():
    """
    Orderly shutdown for application exit.
    """
    return logging.shutdown()


if __name__ == '__main__':

    logger = getLogger('test_facility')

    try:
        record = {'other':'value', 'an_other':'another key value pair' }
        logger.log(logging.CRITICAL, 'Something went wrong message.', extra=record)

    except KeyboardInterrupt:
        pass


