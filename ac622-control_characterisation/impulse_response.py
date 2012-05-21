"""
Script to setup loggers to log a drone's sensor outputs in response to an impulse in pitch.

This script creates an application which sets up loggers to record sensor outputs, does nothing for a period, applies an impulse to the drone, then waits a period before finishing (and therefore removing the logger objects).
This application also logs the commands sent to the drone.

NB - Drone should already be airborne, stable and MUST be passing navdata information before running this script. Suggest using qtdronegui.py to achieve this.
"""

import os
import signal
import sys
import json, socket, time

import Logger

# This makes soure the path which python uses to find things when using import
# can find all our code.
this_file_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(this_file_dir, '..')))

# The magic runes required to import the Qt modules in a platform-independent
# way
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')
QtNetwork = qt.import_module('QtNetwork')


# Variables
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
seq=0
class App(object):
  def __init__(self):
    # Initialise

    self.flag = 1
    log_file = 'command_dump.dat'
    self._log_file = open(log_file, 'w')

    # Create a Qt application loop. We use QCoreApplication because we're not
    # using any GUI features. If we were, we would use a QApplication.
    self.app = QtCore.QCoreApplication(sys.argv)

    # This wires up Ctrl-C to call QApplication.quit()
    signal.signal(signal.SIGINT, lambda *args: self.app.quit())

    # Setup loggers
    theta_logger = Logger.Logger(value = 'theta', port = '5561', log_file = 'theta_dump.dat')
    vx_logger = Logger.Logger(value = 'vx', port = '5561', log_file = 'vx_dump.dat')

    self.loggers = (theta_logger,vx_logger)

    # Create a little 'heartbeat' timer that will call impulse() every so often.
    self.impulse_timer = QtCore.QTimer()
    self.impulse_timer.setInterval(4000) # ms # NB - hover will happen for this long
    self.impulse_timer.timeout.connect(self.impulse)
    self.impulse_timer.start()

    # Create a little 'heartbeat' timer that will call do_nothing() every so often.
    self.do_nothing_timer = QtCore.QTimer()
    self.do_nothing_timer.setInterval(400) # ms # NB - impulse will last for this long
    self.do_nothing_timer.timeout.connect(self.do_nothing)

    # Create a little 'heartbeat' timer that will call hover() every so often.
    self.hover_timer = QtCore.QTimer()
    self.hover_timer.setInterval(5000) # ms # NB - nothing will last for this long
    self.hover_timer.timeout.connect(self.hover)

    # Set up a UDP listening socket on port 5561.
    self.socket = QtNetwork.QUdpSocket()
    if not self.socket.bind(QtNetwork.QHostAddress.Any, 5561):
      raise RuntimeError('Error binding to port: %s' % (self.socket.errorString()))
    self.socket.readyRead.connect(self.socketReadyRead)
#------------------------------------------------------------------------
  def run(self):
    self.app.exec_()
#------------------------------------------------------------------------
  def flip_flag(self):
    """
    Increments state
    """
    states = 3
    if self.flag == states:
      self.flag = 1
    else:
      self.flag = self.flag + 1
    print ("state %s" % (self.flag)) 
#------------------------------------------------------------------------
  def impulse(self):
    """
    Increments state and swaps timers
    """
    self.flip_flag()
    self.impulse_timer.stop()
    self.do_nothing_timer.start()
#------------------------------------------------------------------------
  def do_nothing(self):
    """
    Increments state and swaps timers
    """
    self.flip_flag()
    self.do_nothing_timer.stop()
    self.hover_timer.start()
#------------------------------------------------------------------------
  def hover(self):
    """
    Increments state and swaps timers
    """
    self.flip_flag()
    self.hover_timer.stop()
    self.impulse_timer.start()
#------------------------------------------------------------------------
  def socketReadyRead(self):
    """Called when there is some interesting data to read on the control socket."""

    while self.socket.hasPendingDatagrams():
      sz = self.socket.pendingDatagramSize()
      (data, host, port) = self.socket.readDatagram(sz)
      # Send packets to loggers
      for logger in self.loggers:
        logger.log(data)

      # Send command to drone
      self.send_command()

#------------------------------------------------------------------------
  def send_command(self):
    state = {
                'roll': 0.0,
                'pitch': 0.0,
                'yaw': 0.0,
                'gas': 0.0,
                'take_off': False,
                'reset': False,
                'hover': True,
                                };
    # if want to hover
    if self.flag == 1:
      state['hover'] = True
      state['pitch'] = 0.0
    # if want to impulse
    elif self.flag == 2:
      state['hover'] = False
      state['pitch'] = -1.0
    # if want to do nothing
    elif self.flag == 3:
      state['hover'] = False
      state['pitch'] = 0.0
    else:
      print("states not working - impuse_response.py")

    # Send state to drone
    self.send_state(state)

#------------------------------------------------------------------------
  def send_state(self,state):
    # Send edited state to the drone

    global seq, sock
    seq += 1
    HOST, PORT = ('127.0.0.1', 5560)
    #print('state is', json.dumps({'seq': seq, 'state': state}))
    sock.sendto(json.dumps({'seq': seq, 'state': state}), (HOST, PORT)) 

    # Log commanded pitch and current time
    self._log_file.write(str(time.time()))
    self._log_file.write(' ')
    self._log_file.write(str(state['pitch']))
    self._log_file.write('\n')

if __name__ == '__main__':
  app = App()
  app.run()
