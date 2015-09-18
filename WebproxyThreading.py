import socket
import threading
import SocketServer
import sys
import helper

PROXY_HOST = 'localhost'
PROXY_PORT = 3282
BUFFER_SIZE = 65536

def parseRequest(requestString):
  # parse HTTP request string
  request = helper.Request(requestString)

  # parse host
  hostUrl = 'http://' + request.headers['host']
  url = urlparse(hostUrl)

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
    # Get the http request string
    httpRequest = self.request.recv(BUFFER_SIZE)

    requestInfo = parseRequest(httpRequest)

    print requestInfo

if __name__ == '__main__':
  if len(sys.argv) == 2:
    PROXY_PORT = int(sys.argv[1])

  server = SocketServer.ThreadingTCPServer((PROXY_HOST, PROXY_PORT), ProxyRequestHandler)
  server.serve_forever()