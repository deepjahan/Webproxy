import socket
import helper
import select
import time
import sys
import Queue


PROXY_HOST = 'localhost'
PROXY_PORT = 3282
BUFFER_SIZE = 65536

class Cache:

  def __init__(self):
    self.data = []
    self.length = 0
    self.available = False
    self.content_length = -1

class Proxy:
  input_sockets = []
  output_sockets = []
  # list of client socket
  clients = []
  # socket connection
  forward = {}
  # remote address of remote socket
  key = {}
  # real cache (verified using content length)
  cache = {}
  # temp cache (unverified)
  temp_cache = {}
  # socket message queue
  message_queues = {}

  def verifyCached(self, socket):
    # get remote address of socket
    remoteAddress = self.key[socket]

    # check if content length matches
    if self.temp_cache[socket].length == self.temp_cache[socket].content_length:
      self.cache[remoteAddress] = self.temp_cache[socket]
    else:
      self.temp_cache[socket] = None
      del self.temp_cache[socket]

  def __init__(self, host, port):
    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.server.bind((host, port))
    self.server.listen(128)
    self.input_sockets.append(self.server)
    
  def run(self):
    while 1:
      readable, writable, exceptional = select.select(self.input_sockets, self.output_sockets, [])
      for socket in readable:
        self.current_socket = socket

        if self.current_socket is self.server:
          # ready to accept new connection
          self.accept_current()
        elif self.current_socket in self.input_sockets:
          
          self.data = self.current_socket.recv(BUFFER_SIZE)
          if self.data:
            # current socket has data
            self.receive_current()
          elif self.current_socket not in self.output_sockets:
            # close connection with current socket
            self.close_current(self.current_socket)
      
      for socket in writable:
        try:
          # try to get next message
          next_msg = self.message_queues[socket].get_nowait()
        except:
          # no messages waiting so stop checking for writability
          self.output_sockets.remove(socket)
          if self.forward[socket] is None:
            # close current if forward is closed
            self.close_current(self.current_socket)
        else:
          socket.send(next_msg)

  def accept_current(self):
    connection, clientAddress = self.current_socket.accept()
    self.input_sockets.append(connection)
    self.clients.append(connection)
    self.forward[connection] = None;
    self.message_queues[connection] = Queue.Queue()

  def receive_current(self):

    if self.current_socket in self.clients:
      # current socket is a client
      
      print "\nReceive from client", self.current_socket.getpeername()
      
      # parse data as HTTP request
      request = helper.Request(self.data)

      # parse host
      hostUrl = 'http://' + request.headers['host']
      url = urlparse(hostUrl)

      # get hostname, port, path, method
      remoteHost = url.hostname
      remotePort = url.port or 80
      remotePath = request.path
      remoteMethod = request.command
      
      # use them to identify request cache
      remoteAddress = (remoteMethod, remoteHost, remotePort, remotePath)
      
      # check existing remote socket
      remote_socket = self.forward[self.current_socket]
      
      # if remote socket exist and different port then remove
      if remote_socket is not None and remote_socket.getpeername() is not (remoteHost, remotePort):
        self.input_sockets.remove(remote_socket)

      # check if cache available
      cachedData = self.cache.get(remoteAddress, None)

      # if available, use cache
      if cachedData:
        # loop cache, and send them
        for data in cachedData.data:
          self.message_queues[self.current_socket].put(data)

        # if not in output list, add current socket
        if self.current_socket not in self.output_sockets:
          self.output_sockets.append(self.current_socket)
        return;


      if remote_socket is None:
        # try to create connection to remote server
        try:
          remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          remote_socket.connect((remoteHost, remotePort))
          # pass here if remote socket manage to make connection
          self.message_queues[remote_socket] = Queue.Queue()
          self.key[remote_socket] = remoteAddress
          self.temp_cache[remote_socket] = Cache()

          # add connection between client and remote socket
          self.forward[self.current_socket] = remote_socket
          self.forward[remote_socket] = self.current_socket
          self.input_sockets.append(remote_socket)
        except:
          # host unreachable, send 502 error message
          remote_socket.close()
          self.message_queues[self.current_socket].put(helper.get502())
          
          # if not in output list, add current socket
          if self.current_socket not in self.output_sockets:
            self.output_sockets.append(self.current_socket)
          return;

    else:
      # current socket is remote socket

      if self.temp_cache[self.current_socket].length == 0:
        # this is the first response, try to find content-length
        response = helper.Response(self.data)
        if response.getheader('Content-Length'):
          # content length found, get from header minus first position of \r\n\r\n
          self.temp_cache[self.current_socket].content_length = int(response.getheader('Content-Length')) + self.data.find('\r\n\r\n') + 4
      
      # add to cache
      self.temp_cache[self.current_socket].data.append(self.data)
      self.temp_cache[self.current_socket].length += len(self.data)

      # TODO: modify data

    # get forward socket
    forward_socket = self.forward[self.current_socket]
    # send data that just received
    self.message_queues[forward_socket].put(self.data)

    # if not in output list, add forward socket
    if forward_socket not in self.output_sockets:
      self.output_sockets.append(forward_socket)


  def close_current(self, socket):

    if socket not in self.input_sockets:
      # socket already closed
      return
    
    # remove from input list
    self.input_sockets.remove(socket)

    if socket not in self.clients:
      # socket is remote socket, try to verify the temp cache
      self.temp_cache[socket].available = True
      self.verifyCached(socket)

    # close socket
    socket.close()
    # remove message queue
    del self.message_queues[socket]
    
    # get the forward socket
    forward_socket = self.forward[socket]
    
    if forward_socket:
      # forward socket exists
      self.forward[forward_socket] = None
      if forward_socket not in self.clients:
        # close if forward socket is a remote socket
        self.close_current(forward_socket)

if __name__ == '__main__':
  if len(sys.argv) == 2:
    PROXY_PORT = int(sys.argv[1])
  proxy = Proxy(PROXY_HOST, PROXY_PORT)
  proxy.run();