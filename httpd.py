#!/usr/bin/env python

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import socketserver

# TEST WITH:
# -H "Content-Type: application/json"
# -X
# curl -i -d 'facility=logger' -d 'level=error' -d 'message=Broken pipe' -d '1512203982.239825' -d 'function=validate_email' -d 'exception=LookupError' -d 'userid=person2' -d 'email=p2@emailcom' http://localhost:8080/api/v1/messages

class restHandler(BaseHTTPRequestHandler):
    """
    Logging server.
    Libraries possibly send with: Requests
    Libraries possibly send with: https://docs.python.org/3/library/logging.handlers.html#logging.handlers.HTTPHandler
    Libraries may save to local cache with a separately running client to send the messages to the server.
    This setup would make logging calls independent of network connection and possibly improve performance and protect against surges, but may be unnecessary.
    """

    # Generating timestamps must be true UTC:
    # datetime.datetime.now(datetime.timezone(datetime.timedelta(0), 'UTC'))
    # datetime.datetime.now(datetime.timezone.utc).timestamp()
    # Convert generated timestamp float to %10.6d as it can occasionally come out as %10.5d and we need consistent length.

    def do_POST(self):
        """
        Accept and log messages. Always expects single individual message.
        POST to /api/v1/messages providing these parameters:
        timestamp:  expects UTC timestamp from client although this may introduce slight skew so could just generate on server.
        level:      <number> (accept integer indicating these levels: emerg 70 alert 60 crit 50 error 40 warn 30 notice 25 info 20 debug 10).
        facility:   <string> (name containing usual identifier syntax: alphanumeric, underscore, but no spaces).
        message:    <string> (description of error, needs to be static for each error, no variation from embedded variables).
        name/value: additional arbitrary name/values allowed and will all be logged (clients need to co-ordinate the same names for analysis).
        token:      potential authentication token (probably won't use).
        hmac:       potential HMAC signature.
        Will probably rely on timestamp/level/facility to generate unique reference, but depending on log format uniqueness may be unnecessary.
        """
        if str(self.path) != '/api/v1/messages':
            return self.send_error(404, 'URI Not Allowed (Use /api/v1/messages)')
        if self.headers['content-type'] != 'application/x-www-form-urlencoded':
            return self.send_error(400, 'Bad Request (Requires application/x-www-form-urlencoded)')
        try:
            content = self.rfile.read(int(self.headers['content-length'])) # Content in bytes: self.wfile.write(content).
            content = content.decode() # Defaults to utf-8 string.
            pairs = parse_qs(content, keep_blank_values=True) # Expects minimum of timestamp level facility.
            (timestamp, level, facility) = [pairs.get(key, '') for key in ('timestamp', 'level', 'facility')] # Extracts as lists.
            timestamp = timestamp and timestamp[0] or '' # TODO: Pad trailing zeroes to %10.6d.
            level = level and level[0] or '' # TODO: Client sends as numeric equivalent, even if client library offers named levels.
            # TODO: Sanity check levels? I.e. only allow the specified numeric levels, do not support in-between values?
            facility = facility and facility[0] or '' # Convert from a list of values, possibly undefined, to a reliable scalar.
            if not (facility and level and timestamp): # Cannot log properly without these values.
                return self.send_error(400, 'Bad Request (Requires facility, level, timestamp)')
            self.log(content, timestamp, level, facility) # Write the message.
            self.send_response(201)
            self.send_header('Content-type', 'text/html')
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

    def log(self, content, timestamp, level, facility):
        """
        Log messages to storage.
        content contains the full url-encoded string defining all content for the message.
        timestamp, level, facility are all decoded out of the content string.
        The permanent record will probably be day based log files named as: YYYYMMDD-level-facility.
        Potentially could log messages individually named as: YYYYMMDD-HHMMSS.uuuuuu-level-facility.
        May drop messages to individual files for reliability and speed and run a worker to clean them up continually to day based log file.
        Log probably kept in url encoded format prefixed with unique reference / index for sorting and filtering.
        """
        print('-'.join((timestamp, level, facility)) + ': ' + content)

        # E.g:
        # determine filename prefix and day string
        # if day directory not present create
        # if prefix filename not present create
        # log to prefix filename

        # ???
        # loggers = dict()
        # if not level in loggers: loggers[level] = dict()
        # if not facility in loggers[level]: loggers[level][facility] = TimedRotatingFileHandler()
        # Subclass BaseRotatingHandler or TimedRotatingFileHandler in loggers where the default name is level-facility.
        # On daily rotation move to YYMMDD-level-facility.
        return

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
