import socket
import parser
import select
import time
import sys
from urlparse import urlparse

PROXY_HOST = 'localhost'
PROXY_PORT = 3282
BUFFER_SIZE = 65536

from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime

def get502():
  HTTP_RESPONSE_502 = """HTTP/1.0 502 Bad Gateway
Date: %s
Server: Apache/2.2.15 (CentOS)
X-Powered-By: PHP/5.6.4
Content-Length: 0
Connection: close
Content-Type: text/html; charset=UTF-8
"""
  now = datetime.now()
  stamp = mktime(now.timetuple())
  return HTTP_RESPONSE_502 % (format_date_time(stamp))



now = datetime.now()
stamp = mktime(now.timetuple())
print format_date_time(stamp) 

class Proxy:
  sockets = []
  clients = []
  forward = {}

  def __init__(self, host, port):
    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.server.bind((host, port))
    self.server.listen(128)
    self.sockets.append(self.server)

  def run(self):
    while 1:
      readable, writable, exceptional = select.select(self.sockets, [], [])
      for socket in readable:
        self.current_socket = socket
        if self.current_socket is self.server:
          # ready to accept new connection
          self.accept_current()
        elif self.current_socket in self.sockets:
          self.data = self.current_socket.recv(BUFFER_SIZE)
          if self.data:
            # current socket has data
            self.receive_current()
          else:
            # close connection with current socket
            self.close_current()
          

  def accept_current(self):
    connection, clientAddress = self.current_socket.accept()
    connection.setblocking(0)
    print clientAddress, "has connected"
    self.sockets.append(connection)
    self.clients.append(connection)
    self.forward[connection] = None;

  def receive_current(self):

    if self.current_socket in self.clients:
      # current socket is a client
      
      print "\nReceive from client", self.current_socket.getpeername()
      
      print "------"
      print self.data
      print "------\n"
      # parse data as HTTP request
      request = parser.Request(self.data)

      # parse host
      hostUrl = 'http://' + request.headers['host']
      url = urlparse(hostUrl)

      # get hostname and port
      remoteHost = url.hostname
      remotePort = url.port or 80

      # remove existing remote socket
      remote_socket = self.forward[self.current_socket]
      
      if remote_socket is not None and remote_socket.getpeername() is not (remoteHost, remotePort):
        self.sockets.remove(remote_socket)
        remote_socket.close()
        del self.forward[remote_socket]
        remote_socket = None

      if remote_socket is None:
        try:
          remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          remote_socket.connect((remoteHost, remotePort))
          
          # add connection between client and remote socket
          self.forward[self.current_socket] = remote_socket
          self.forward[remote_socket] = self.current_socket
          self.sockets.append(remote_socket)
        except:
          # host unreachable, send 502 error message
          remote_socket.close()
          self.current_socket.send(get502())
          self.close_current()
          return;

    else:
      # current socket is remote socket
      
      print "\nReceive from remote", self.current_socket.getpeername(), ' requested by ', self.forward[self.current_socket].getpeername()
      """
      print "------"
      print self.data
      print "------\n"
      """
      # parse data as HTTP response
      response = parser.Response(self.data)

      # TODO: modify data

    self.forward[self.current_socket].send(self.data)



  def close_current(self):
    print self.current_socket.getpeername(), "has disconnected"

    # remove from clients and sockets list
    self.sockets.remove(self.current_socket)
    if self.current_socket in self.clients:
      self.clients.remove(self.current_socket)

    # close current socket
    self.current_socket.close()
    
    # close remote socket
    remote_socket = self.forward[self.current_socket]
    if remote_socket:
      remote_socket.close()
      self.sockets.remove(remote_socket)
      del self.forward[remote_socket]

    del self.forward[self.current_socket]



if __name__ == '__main__':
  if len(sys.argv) == 2:
    PROXY_PORT = int(sys.argv[1])
  proxy = Proxy(PROXY_HOST, PROXY_PORT)
  proxy.run();