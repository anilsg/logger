#!/usr/bin/env python
# Python 3.6.3
# curl -i -d 'facility=facility_name' -d 'level=40' -d 'message=error_name' -d 'datestamp=20171203-123456.123456' -d 'additional_key=additional_value' http://localhost:8080/api/v1/messages

import logging, logging.handlers
import datetime
import random

# TODO: SSL and basic auth
# TODO: Catch server down exception

host = 'localhost:8080'
route = '/api/v1/messages'

# Can read userid/password from a file, if don't want to hard code.

def getLogger(facility):
    logger = logging.getLogger(facility) # Standard library logger.
    http_handler = logging.handlers.HTTPHandler(host, route, method='POST') # secure=True, context=ssl.SSLContext, credentials=(userid, password)
    http_handler.setLevel(logging.INFO) # Using logging.DEBUG or 0 may raise the rate of message passing too high.
    http_handler.raiseExceptions = False # Suppress exceptions in use.
    logger.addHandler(http_handler) # Log everything through this handler without filtering.
    return logger # Pass back the logger object.

# name=remote_logger
# msg=new_message
# levelname=CRITICAL
# levelno=50
# created=1512347566.426008   datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
# datestamp=20171204-003246

if __name__ == '__main__':

    logger = getLogger('test_facility')

    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        record = {}
        record['datestamp'] = '{0:%Y%m%d-%H%M%S}.{1}'.format(now, now.microsecond)
        record['facility'] = logger.name
        record['level'] = str(logging.CRITICAL)
        # record['message'] = 'new_message'
        record['other'] = 'other key value pair'
        record['an_other'] = 'yet other key value pair'
        logger.log(logging.CRITICAL, 'new_message', extra=record)

    except KeyboardInterrupt:
        pass

    logging.shutdown()
