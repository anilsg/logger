#!/usr/bin/env python
# Python 3.6.3

import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

# import socketserver

class restHandler(BaseHTTPRequestHandler):
    """
    Handle requests to REST API to log a message and retrieve messages.
    Use basic auth over HTTPS?
    """

    # datetime.datetime.now(datetime.timezone(datetime.timedelta(0), 'UTC'))
    # datetime.datetime.now(datetime.timezone.utc).timestamp()
    # '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now())

    def do_POST(self):
        """
        Accept and log individual messages in url-encoded format.
        Rely on datetime/level/facility to generate unique reference.
        Messages must POST to /api/v1/messages with these parameters:
        datetime:   <YYYYMMDD-HHMMSS.uuuuuu>.
        level:      <number> (accept integer indicating these levels: emerg 70 alert 60 crit 50 error 40 warn 30 notice 25 info 20 debug 10).
        facility:   <string> (name containing usual identifier syntax: alphanumeric, underscore, but no spaces).
        message:    <string> (static description of error, no variation from embedded variables, to ensure occurences can be counted).
        name/value: additional arbitrary name/values allowed and will be logged (clients need to co-ordinate the same names for analysis).
        token:      authentication token?
        hmac:       HMAC signature?
        E.g. curl -i -d 'facility=facility_name' -d 'level=40' -d 'message=error_name' -d 'datetime=20171203-123456.123456' -d 'additional_key=additional_value' http://localhost:8080/api/v1/messages
        """
        if str(self.path) != '/api/v1/messages':
            return self.send_error(404, 'URI Not Allowed (Use /api/v1/messages)')
        if self.headers['content-type'] != 'application/x-www-form-urlencoded':
            return self.send_error(400, 'Bad Request (Requires application/x-www-form-urlencoded)')
        try:
            content = self.rfile.read(int(self.headers['content-length'])) # Content in bytes: self.wfile.write(content).
            content = content.decode() # Defaults to utf-8 string.
            pairs = parse_qs(content, keep_blank_values=True) # Expects minimum of datetime, level, facility.
            (datestamp, level, facility, message) = [pairs.get(key, '') for key in ('datetime', 'level', 'facility', 'message')] # Extracts as lists.
            datestamp = datestamp and datestamp[0] or '' # Extract first element of list. TODO: Supply default of UTC right now.
            if len(datestamp) != 22: # Expecting YYYYMMDD-HHMSS.uuuuuu.
                return self.send_error(400, 'Bad Request (Datetime must be YYYYMMDD-HHMMSS.uuuuuu)')
            level = level and level[0] or '00' # Take first item in list or generate default: 00=LOG_UNSPEC.
            if len(level) != 2 or not level.isdigit(): # 70=LOG_EMERG, 60=LOG_ALERT, 50=LOG_CRIT, 40=LOG_ERR, 30=LOG_WARNING 25=LOG_NOTICE, 20=LOG_INFO, 10=LOG_DEBUG.
                return self.send_error(400, 'Bad Request (Level must be double digit numeric)')
            facility = facility and facility[0] or '' # Convert from a list of values, possibly undefined, to a reliable scalar.
            if not facility: # Pointless to log without facility name to show origin.
                return self.send_error(400, 'Bad Request (Requires facility name)')
            message = message and message[0] or 'no_message' # Convert from a list of values, possibly undefined, to a reliable scalar.
            if not self.log(content, datestamp, level, facility, message): # Write the message.
                return self.send_error(500, 'Server error (failed to log)')
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

    def log(self, content, datestamp, level, facility, message):
        """
        Log single message to storage and return to complete log request quickly.
        content contains the full url-encoded string defining all content for the message.
        datestamp, level, facility, message are all decoded out of the content string already.
        Messages are logged as an individual file to a cache directory determined by the content.
        Separately managed worker processes can then clean those up into individual log files.
        This avoids having sub-processes and provides reliable logging when processes get killed.
        The permanent record could be day based log files named as: YYYYMMDD-level-facility.
        Could log messages individually YYYYMMDD-HHMMSS.uuuuuu-level-facility for reliability and run a worker to clean them up continually to day based log file.
        Log kept in url encoded format prefixed with unique reference / index for sorting and filtering.
        """
        logline ='{datetime}-{level}-{facility}: {message} {content}'.format(datetime=datestamp, level=level, facility=facility, message=message, content=content)
        print(logline)

        # 1: extract required strings for logging
        # 2: determine file name and content
        # 3: write to appropriate cache directory and return

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

        # Queues can deliver messages out of order, and can become corrupted if processes fail while using the queue.

        return logline

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

