# Some magic for Python3
try:
  import SocketServer as socketserver
except ImportError:
  import socketserver

import logging
import sys
import threading

class ATCommandUDPHandler(socketserver.BaseRequestHandler):
  def command(self, cmd):
    logging.info('Got command: %s' % (cmd,))

  def handle(self):
    commands = self.request[0].strip().split('\n')
    socket = self.request[1]

    logging.info('%s -> %s' % (self.client_address, repr(commands)))
    for command in commands:
      self.command(command)

class ATCommandListener(threading.Thread):
  def __init__(self):
    super(ATCommandListener, self).__init__()

    self.should_quit = False
    self.cv = threading.Condition()

    (bind_host, bind_port) = '127.0.0.1', 5556
    self._server = socketserver.UDPServer((bind_host, bind_port),
        ATCommandUDPHandler)
  
  def run(self):
    self._server.serve_forever()

def serve():
  # Create an AT command listener
  at_listener = ATCommandListener()
  at_listener.daemon = True
  at_listener.start()

  # Wait for the quit command
  at_listener.cv.acquire()
  while not at_listener.should_quit:
    at_listener.cv.wait(0.5)
  at_listener.cv.release()

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  serve()
