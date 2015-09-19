import socket
import threading
import SocketServer
import sys
import time
import hashlib
from helper import Request, Response

PROXY_HOST = 'localhost'
PROXY_PORT = 3282
BUFFER_SIZE = 4096

class ProxyRequestHandler(SocketServer.BaseRequestHandler):

  cache_manifest = {}

  def request_from_cache(self, md5):
    self.remote.close()
    with open(md5, 'r') as f:
      while 1:
        data = f.read(BUFFER_SIZE)
        if data:
          self.request.send(data)
        else:
          break
      self.request.close()


  def request_and_cache(self, md5, message):
    # send the http request
    self.remote.send(message)

    # cache available but not ready
    self.cache_manifest[md5] = False

    with open(md5, 'w') as f:
      f.seek(0)
      f.truncate()
      # receive data from remote socket
      try:
        while 1:
          data = self.remote.recv(BUFFER_SIZE)
          if data:
            self.request.send(data)
            f.write(data)
          else:
            break
      except socket.error:
        pass

      self.remote.close()
      self.request.close()

    # cache available and ready
    self.cache_manifest[md5] = True
    

  def request_only(self, message):
    # send the http request
    self.remote.send(message)

    # receive data from remote socket
    try:
      while 1:
        data = self.remote.recv(BUFFER_SIZE)
        if data:
          self.request.send(data)
        else:
          break
    except socket.error:
      pass

    self.remote.close()
    self.request.close()


  def handle(self):
    try:
      print "Connected:", self.client_address
      # get the http request string
      httpRequest = self.request.recv(BUFFER_SIZE)

      print httpRequest

      if not httpRequest:
        self.request.close()
        return
      # get information about the request
      requestInfo = Request(httpRequest, self.client_address).get_info()


      try:
        # make connection with remote address
        self.remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.remote.connect((requestInfo.get('host', ''), requestInfo.get('port', 0)))
        self.remote.setblocking(0)
        self.remote.settimeout(3.0)
        # request

        hash = str(hashlib.md5(httpRequest).hexdigest())

        if self.cache_manifest.get(hash, None):
          print '### get from cache'
          self.request_from_cache(hash)
        elif requestInfo.get('method', '') == 'GET' and self.cache_manifest.get(hash, None) is None:
          print '### get and cache'
          self.request_and_cache(hash, httpRequest)
          print '### done caching'
        else:
          print '### get only'
          self.request_only(httpRequest)
          print '### done get'
        
      except socket.error as msg:
        print '### socket error', msg 
        # send 502 message
        if self.request:
          self.request.send(Request().get_error(502))
          self.request.close()

        if self.remote:
          self.remote.close()

    except KeyboardInterrupt:
      self.request.close()  


if __name__ == '__main__':
  if len(sys.argv) == 2:
    PROXY_PORT = int(sys.argv[1])

  server = SocketServer.ThreadingTCPServer((PROXY_HOST, PROXY_PORT), ProxyRequestHandler)
  server.allow_reuse_address=True
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    server.shutdown()
