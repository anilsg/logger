#!/usr/bin/env python

from http.server import BaseHTTPRequestHandler, HTTPServer

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
    This setup would make logging calls independent of network connection and possibly improve performance and protect against surges.
    However, it may just not be required.
    """

    def do_POST(self):
        """
        Accept and log messages.
        Always expects single individual message.
        """
        try:
            content = self.rfile.read(int(self.headers['content-length'])) # Content in bytes: self.wfile.write(content).
            content = content.decode() # Defaults to utf-8 string.
            self.send_response(201)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-length', str(len(content)))
            self.end_headers()
            self.wfile.write(bytes(content, "utf-8"))
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
            response = self.path
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-length', str(len(response)))
            self.end_headers()
            self.wfile.write(bytes(response, "utf-8"))
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

if __name__ == '__main__':
    httpd = HTTPServer(('', 8080), restHandler) # httpd.timeout = 10 # Simple attempt to force timeout fails.
    print(str(httpd))
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass
    httpd.server_close()

    ## Using HTTP for now, implementing HTTPS is a simple improvement.
    ## from http.server import HTTPServer, BaseHTTPRequestHandler
    ## import ssl
    ## httpd = HTTPServer(('localhost', 4443), SimpleHTTPRequestHandler)
    ## httpd.socket = ssl.wrap_socket (httpd.socket, keyfile="path/to/key.pem", certfile='path/to/cert.pem', server_side=True)
    ## httpd.serve_forever()
