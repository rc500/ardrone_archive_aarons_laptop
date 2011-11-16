"""A simple example of sending control commands to the drone via qtdronequi.

The qtdronegui program can accept control commands for the drone over the
network. It listens on UDP port 5560 for JSON formatted control commands.

This program serves as an example of communicating with the drone.

"""

# Import the standard library modules which we use
import json   # for converting the control state into a string to send to the GUI
import socket # for sending the string to the GUI
import time   # for sleeping for a set period of time

"""A global socket object which can be used to send commands to the GUI program."""
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

"""A global sequence counter. The GUI uses this to determine if two commands
have been received in the wrong order: the command with the largest (latest)
sequence will always 'win'."""
seq = 0

def send_state(state):
  """Send the state dictionary to the drone GUI.

  state is a dictionary with (at least) the keys roll, pitch, yaw, gas,
  take_off, reset and hover. The first four are floating point values on the
  interval [-1,1] which specify the setting of the corresponding attitude
  angle/vertical speed. The last three are True or False to indicate if that
  virtual 'button' is pressed.

  """
  global seq, sock
  seq += 1
  HOST, PORT = ('127.0.0.1', 5560)
  print('state is', json.dumps({'seq': seq, 'state': state}))
  sock.sendto(json.dumps({'seq': seq, 'state': state}), (HOST, PORT))

def press(state, button):
  """Simulate pressing a button.

  state is the current state of the controls.

  button is a string which is one of: 'reset' or 'take_off'.

  This function simulate pressing the correspinding button by setting the state
  of that button to true, waiting for half a second, and setting it back to
  false.

  This function returns the new state.

  Idiomatic use is to pass the current state and set the current state to the
  return value. e.g.:
  
    state = {
      'roll': # ... 
    }

    state = press(state, 'reset')
    state = press(state, 'take_off')
    # ... etc

  FIXME: No attempt to *verify* the value of button is made.

  """

  # Press the button
  state[button] = True
  send_state(state)

  # Wait
  time.sleep(0.5)

  # Release the button
  state[button] = False
  send_state(state)

def main():
  """The main entry point of the progam. Called by the bootstrap code at the
  bottom of the file.

  """

  # Initialse a dictionary corresponding to the controls current state.
	state = {
      'roll': 0.0,
      'pitch': 0.0,
      'yaw': 0.0,
      'gas': 0.0,
      'take_off': False,
      'reset': False,
      'hover': True,
  };

  # Reset the drone
  state = press(state, 'reset')

  # Wait 5 seconds for the drone to reset
	time.sleep(5)

  # Take off
  state = press(state, 'take_off')

  # Wait 10 seconds
	time.sleep(10)

  # Press take off again (paradoxically, this will land the drone).
  state = press(state, 'take_off')

if __name__ == '__main__':
  main()
