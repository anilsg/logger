#!/usr/bin/env python
# Python 3.6.3

"""
Remote logging server.
TODO: Basic auth over SSL.
TODO: Forking.
"""

from os import path
import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

# import socketserver

class restHandler(BaseHTTPRequestHandler):
    """
    Handle requests to REST API to log messages and retrieve messages.

    POST: Logging Messages.
    This server receives HTTP POST with the log message from remote clients.
    Messages are stored in temporary cache and server immediately returns response to client.
    Further aggregation of messages is managed by separate process to ensure fast server response.
    """

    cache_path = '/srv/http/logger/cache' # This is the cache destination for all messages received.

    def do_POST(self):
        """
        Accept and store individual messages in url-encoded format, as sent by logging.handlers.HTTPHandler.

        Messages must POST to /api/v1/messages with these parameters.
        Parameters align to those generated and used by logging standard library module.

        created:    Is a datetime timestamp generated by the logger like this: 1512386686.0873692.
        name:       Is the facility name given to logger on creation, using usual identifier syntax: alphanumeric, underscore, no spaces.
        levelno:    The usual logging level numeric equivalent: emerg=70 alert=60 crit=50 error=40 warn=30 notice=25 info=20 debug=10.
        msg:        Static string description of error, without embedded formatting or variables, to support counting like errors.
        name/value: Additional arbitrary name/values allowed and will be logged (clients need to co-ordinate the same names for analysis).
        token:      Authentication token not supported.
        hmac:       HMAC signature not supported.

        E.g. curl -i -d 'name=facility_name' -d 'levelno=40' -d 'msg=error_name' -d 'created=1512386686.123456' -d 'additional_key=additional_value' http://localhost:8080/api/v1/messages
        Rely on datetime/level/facility to generate unique reference.
        """
        if str(self.path) != '/api/v1/messages': # Only accept POST requests to this single API.
            return self.send_error(404, 'URI Not Allowed (Use /api/v1/messages)') # Descriptive error response.
        if self.headers['content-type'] != 'application/x-www-form-urlencoded': # Only accept url-encoded requests.
            return self.send_error(400, 'Bad Request (Requires application/x-www-form-urlencoded)') # Descriptive response.
        try:
            content = self.rfile.read(int(self.headers['content-length'])) # Content arrives in unencoded bytes.
            content = content.decode() # Defaults to utf-8 string, which should have url-encoded variables.
            self.log(content) # Write the message to the cache.
            self.send_response(201) # Respond OK.
            self.send_header('Content-type', 'text/plain')
            ## self.send_header('Content-length', str(len(content))) # No need to send content back.
            self.end_headers()
            ## self.wfile.write(bytes(content, "utf-8"))
        except Exception as e: # Something went wrong, send description back.
            self.send_error(500, 'Server error: ' + repr(e))
        return

    def do_GET(self):
        """
        Return logged messages.
        Support multiple routes providing by the minute, by the hour, by the day.
        Could be used to download portions of the logs.
        Not yet implemented.
        """
        try:
            content = self.path
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-length', str(len(content)))
            self.end_headers()
            self.wfile.write(bytes(content, "utf-8"))
        except:
            self.send_error(500)
        return

    def do_DELETE(self):
        """
        Flush messages.
        Possible deliberate flush, although this would normally be automated.
        Consider retaining archived records dependent on available space and allow restore.
        """
        self.send_error(501) # Not yet implemented.

    def log(self, content):
        """
        Log single message to cache storage and return to complete log request quickly.
        content contains the full url-encoded string defining all content for the message.
        Messages are logged as individual files named YYYYMMDD-HHMMSS.uuuuuu-level-facility to the cache directory in self.cache_path.
        Separately managed worker processes then aggregate those into individual log files organised for retrieval.
        This avoids managing sub-processes in this server and provides reliable logging even when processes get killed.
        Queues deliver messages out of order, and can become corrupted if processes fail while using the queue.
        TODO: Replace newlines with spaces in content string.
        TODO: Default to UTC now() if created timestamp is missing.
        TODO: Catch exceptions and report sensibly.
        """
        print(content, '\n') ## Testing / debug.

        # Decode url-encoded pairs.
        pairs = parse_qs(content, keep_blank_values=True) # Extract from url-encoded string into lists of values.
        (created, levelno, facility, message) = [pairs.get(key, '') for key in ('created', 'levelno', 'name', 'msg')] # Extracts as lists.
        
        # Check and process supplied parameters.
        created = created and float(created[0]) or 0.0 # Take first list element and convert to float timestamp.
        created = datetime.datetime.fromtimestamp(created, tz=datetime.timezone.utc) # Convert epoch stamp to UTC datetime.
        created = '{0:%Y%m%d-%H%M%S}.{1}'.format(created, created.microsecond) # And convert to string format required for storing.
        if len(created) != 22: # Expecting YYYYMMDD-HHMSS.uuuuuu.
            return self.send_error(400, 'Bad Request (created must be timestamp ssssssssss.uuuuuu)')

        levelno = levelno and levelno[0] or '00' # Take first item in list or generate default: 00=LOG_UNSPECIFIED. Retain as string.
        if len(levelno) != 2 or not levelno.isdigit(): # 70=LOG_EMERG, 60=LOG_ALERT, 50=LOG_CRIT, 40=LOG_ERR, 30=LOG_WARNING 25=LOG_NOTICE, 20=LOG_INFO, 10=LOG_DEBUG.
            return self.send_error(400, 'Bad Request (levelno must be double digit numeric)')

        facility = facility and facility[0] or 'no_facility' # Convert from a list of values, possibly undefined, to a reliable scalar.
        message = message and message[0] or 'no_message' # Choosing not to complain if really useful parameters are not supplied.

        # Construct cached message name and internal information.
        filename ='{created}-{levelno}-{facility}'.format(created=created, levelno=levelno, facility=facility)
        logline ='{filename}:{message}:{content}'.format(filename=filename, message=message, content=content)
        print(logline, '\n\n') ## Testing / debug.

        # Write the message to the temporary cache.
        with open(path.join(self.cache_path, filename), mode='a', encoding='utf-8') as outfile:
            outfile.write(logline) # Append rather than write protects against rare collisions and should work, retaining both messages.

if __name__ == '__main__':
    httpd = HTTPServer(('', 8080), restHandler) # httpd.timeout = 10 # Simple attempt to force timeout fails.
    print(str(httpd))
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass
    httpd.server_close()


    ## HTTPS recipe:
    ## https://stackoverflow.com/questions/20470831/https-server-with-python
    ## Using HTTP for now, implementing HTTPS is a simple improvement.
    ## from http.server import HTTPServer, BaseHTTPRequestHandler
    ## import ssl
    ## httpd = HTTPServer(('localhost', 4443), SimpleHTTPRequestHandler)
    ## httpd.socket = ssl.wrap_socket (httpd.socket, keyfile="path/to/key.pem", certfile='path/to/cert.pem', server_side=True)
    ## httpd.serve_forever()

    ## Forking recipe:
    ## class ForkingHTTPServer(socketserver.ForkingMixIn, HTTPServer):
    ##     def finish_request(self, request, client_address):
    ##         request.settimeout(30)
    ##         HTTPServer.finish_request(self, request, client_address)
    ## 
    ## if __name__ == '__main__':
    ##     httpd = ForkingHTTPServer(('', 8080), restHandler)
    ##     print(str(httpd))
    ##     try: httpd.serve_forever()
    ##     except KeyboardInterrupt: pass
    ##     httpd.socket.close()

