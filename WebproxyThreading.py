import socket
import threading
import SocketServer
import sys
import helper
import urlparse

PROXY_HOST = 'localhost'
PROXY_PORT = 3282
BUFFER_SIZE = 65536

def parseRequest(requestString):
  # parse HTTP request string
  request = helper.Request(requestString)

  # parse host

  try:
    hostUrl = 'http://' + request.headers['host']
    url = urlparse.urlparse(hostUrl)
  except:
    return {}

  remote = {}
  # get hostname, port, path, method
  remote['host'] = url.hostname
  remote['port'] = url.port or 80
  remote['path'] = request.path
  remote['method'] = request.command

  return remote

class ProxyRequestHandler(SocketServer.BaseRequestHandler):

  def handle(self):
    print "Connected:", self.client_address
    # get the http request string
    httpRequest = self.request.recv(BUFFER_SIZE)
    if not httpRequest:
      self.request.close()
      return
    # get information about the request
    requestInfo = parseRequest(httpRequest)

    try:
      remoteSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      remoteSocket.connect((requestInfo.get('host', ''), requestInfo.get('port', 0)))
      # send the http request
      remoteSocket.send(httpRequest)

      # receive data from remote socket
      while 1:
        data = remoteSocket.recv(BUFFER_SIZE)
        if data:
          self.request.send(data)
        else:
          break

      remoteSocket.close()
      self.request.close()

    except socket.error:
      # send 502 message
      if self.request:
        self.request.send(helper.get502())
        self.request.close()

      if remoteSocket:
        remoteSocket.close()
      


if __name__ == '__main__':
  if len(sys.argv) == 2:
    PROXY_PORT = int(sys.argv[1])

  server = SocketServer.ThreadingTCPServer((PROXY_HOST, PROXY_PORT), ProxyRequestHandler)
  server.allow_reuse_address=True
  server.serve_forever()