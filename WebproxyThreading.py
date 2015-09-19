import socket
import threading
import SocketServer
import sys
from helper import Request, Response

PROXY_HOST = 'localhost'
PROXY_PORT = 3282
BUFFER_SIZE = 65536

class ProxyRequestHandler(SocketServer.BaseRequestHandler):

  def handle(self):
    try:
      print "Connected:", self.client_address
      # get the http request string
      httpRequest = self.request.recv(BUFFER_SIZE)

      if not httpRequest:
        self.request.close()
        return
      # get information about the request
      requestInfo = Request(httpRequest, self.client_address).get_info()


      try:
        # make connection with remote address
        remoteSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remoteSocket.connect((requestInfo.get('host', ''), requestInfo.get('port', 0)))
        remoteSocket.settimeout(10.0)

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
          self.request.send(Request().get_error(502))
          self.request.close()

        if remoteSocket:
          remoteSocket.close()

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
