from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
from httplib import HTTPResponse

class Request(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

class FakeSocket():
    def __init__(self, response_str):
        self._file = StringIO(response_str)
    def makefile(self, *args, **kwargs):
        return self._file

class Response(HTTPResponse):
  def __init__(self, response_str):
    source = FakeSocket(response_str)
    HTTPResponse.__init__(self, source)
    self.begin()

# Request
# error_code 
# command    GET/POST
# path       PATH
# request_version "HTTP/1.0"
# headers   "Headers"
# headers.keys() 
# headers['host']

# Response
# status    CODE
# getheader('Content-Length')
# read(len(response_str)) 