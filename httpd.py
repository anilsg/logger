#!/usr/bin/env python
# Python 3.6.3

import sys
from os import path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

# import socketserver

class restHandler(BaseHTTPRequestHandler):
    """
    Handle requests to REST API to log a message and retrieve messages.
    Use basic auth over HTTPS?
    """

    cache_path = '/srv/http/logger/cache'

    # datetime.datetime.now(datetime.timezone(datetime.timedelta(0), 'UTC'))
    # datetime.datetime.now(datetime.timezone.utc).timestamp()
    # '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now())

    def do_POST(self):
        """
        Accept and log individual messages in url-encoded format.
        Rely on datestamp/level/facility to generate unique reference.
        Messages must POST to /api/v1/messages with these parameters:
        datestamp:  <YYYYMMDD-HHMMSS.uuuuuu>.
        level:      <number> (accept integer indicating these levels: emerg 70 alert 60 crit 50 error 40 warn 30 notice 25 info 20 debug 10).
        facility:   <string> (name containing usual identifier syntax: alphanumeric, underscore, but no spaces).
        message:    <string> (static description of error, no variation from embedded variables, to ensure occurences can be counted).
        name/value: additional arbitrary name/values allowed and will be logged (clients need to co-ordinate the same names for analysis).
        token:      authentication token?
        hmac:       HMAC signature?
        E.g. curl -i -d 'facility=facility_name' -d 'level=40' -d 'message=error_name' -d 'datestamp=20171203-123456.123456' -d 'additional_key=additional_value' http://localhost:8080/api/v1/messages
        """
        if str(self.path) != '/api/v1/messages':
            return self.send_error(404, 'URI Not Allowed (Use /api/v1/messages)')
        if self.headers['content-type'] != 'application/x-www-form-urlencoded':
            return self.send_error(400, 'Bad Request (Requires application/x-www-form-urlencoded)')
        try:
            content = self.rfile.read(int(self.headers['content-length'])) # Content in bytes: self.wfile.write(content).
            content = content.decode() # Defaults to utf-8 string.
            self.log(content) # Write the message.
            self.send_response(201)
            self.send_header('Content-type', 'text/plain')
            ## self.send_header('Content-length', str(len(content))) # No need to send content back.
            self.end_headers()
            ## self.wfile.write(bytes(content, "utf-8"))
        except Exception as e:
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
        Log single message to storage and return to complete log request quickly.
        content contains the full url-encoded string defining all content for the message.
        datestamp, level, facility, message are all decoded out of the content string already.
        Messages are logged as individual files named YYYYMMDD-HHMMSS.uuuuuu-level-facility to the cache directory in self.cache_path.
        Separately managed worker processes then aggregate those into individual log files named level-facility in individual directories named YYYYMMDD.
        This avoids managing sub-processes and provides reliable logging even when processes get killed.
        Queues can deliver messages out of order, and can become corrupted if processes fail while using the queue.
        Log kept in url encoded format prefixed with unique reference / index for sorting and filtering and to save work decoding and reformatting.
                return self.send_error(500, 'Server error (failed to log)')
        """
        # TODO: Replace newlines with spaces in content string.
        print(content)
        pairs = parse_qs(content, keep_blank_values=True) # Extract from url-encoded into lists.
        (datestamp, level, facility, message) = [pairs.get(key, '') for key in ('datestamp', 'level', 'facility', 'message')] # Extracts as lists.
        datestamp = datestamp and datestamp[0] or '' # Extract first element of list. TODO: Default to UTC now if missing.
        if len(datestamp) != 22: # Expecting YYYYMMDD-HHMSS.uuuuuu.
            return self.send_error(400, 'Bad Request (datestamp must be YYYYMMDD-HHMMSS.uuuuuu)')
        level = level and level[0] or '00' # Take first item in list or generate default: 00=LOG_UNSPEC.
        if len(level) != 2 or not level.isdigit(): # 70=LOG_EMERG, 60=LOG_ALERT, 50=LOG_CRIT, 40=LOG_ERR, 30=LOG_WARNING 25=LOG_NOTICE, 20=LOG_INFO, 10=LOG_DEBUG.
            return self.send_error(400, 'Bad Request (Level must be double digit numeric)')
        facility = facility and facility[0] or 'no_facility' # Convert from a list of values, possibly undefined, to a reliable scalar.
        message = message and message[0] or 'no_message' # Choosing not to complain if really useful parameters are not supplied.
        filename ='{datestamp}-{level}-{facility}'.format(datestamp=datestamp, level=level, facility=facility) # These are utf-8 strings now.
        logline ='{filename}:{message}:{content}'.format(filename=filename, message=message, content=content)
        print(logline)
        # TODO: Try to catch exceptions and report sensibly.
        with open(path.join(self.cache_path, filename), mode='a', encoding='utf-8') as outfile:
            outfile.write(logline) # Append protects against rare collisions and retains both messages.

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

