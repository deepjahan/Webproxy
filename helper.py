from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
from httplib import HTTPResponse
from urlparse import urlparse
import time

class Request(BaseHTTPRequestHandler):
  def __init__(self, request_text='', client=('', 80)):
    self.rfile = StringIO(request_text)
    self.raw_requestline = self.rfile.readline()
    self.wfile = StringIO()
    self.error_code = self.error_message = None
    self.client_address = client
    self.parse_request()
    self.request_version = 'HTTP/1.0'

  def log_message(self, format, *args):
    pass

  def get_info(self):
    # parse host
    try:
      hostUrl = 'http://' + self.headers['host']
      url = urlparse(hostUrl)
    except:
      return {}

    info = {}
    # get hostname, port, path, method
    info['host'] = url.hostname
    info['port'] = url.port or 80
    info['path'] = self.path
    info['method'] = self.command
    info['time'] = time.time()
    return info

  def get_error(self, code):
    self.send_error(code)
    return self.wfile.getvalue()

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