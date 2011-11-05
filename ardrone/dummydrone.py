# Some magic for Python3
try:
  import SocketServer as socketserver
except ImportError:
  import socketserver

import logging
import sys
import threading

class DroneUDPHandler(socketserver.BaseRequestHandler):
  def handle(self):
    data = self.request[0].strip()
    socket = self.request[1]

    logging.info("%s wrote:" % (str(self.client_address[0]),))
    logging.info(data)

    socket.sendto(data.upper(), self.client_address)

class ServeThread(threading.Thread):
  def run(self):
    HOST, PORT = 'localhost', 5556
    server = socketserver.UDPServer((HOST, PORT), DroneUDPHandler)
    server.serve_forever()

def serve():
  st = ServeThread()
  st.start()

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  serve()
