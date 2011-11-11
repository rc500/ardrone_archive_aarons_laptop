import pygame, json, math, socket

# Axes
ROLL_AXIS         = 0 # Xbox: left stick H
PITCH_AXIS        = 1 # Xbox: left stick V
HOVER_AXIS        = 2 # Xbox: left trigger
YAW_AXIS          = 3 # Xbox: right stick H
GAS_AXIS          = 4 # Xbox: right stick V

# Buttons
RESET_BUTTON      = 7 # Xbox: 'Start'
QUIT_BUTTON       = 6 # Xbox: 'Back'
TAKE_OFF_BUTTON   = 8 # Xbox: 'Xbox logo'

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

seq = 0
def send_state(state):
  global seq, sock
  seq += 1
  HOST, PORT = ('127.0.0.1', 5560)
  sock.sendto(json.dumps({'seq': seq, 'state': state}), (HOST, PORT))

def main():
  pygame.init()

  n_joysticks = pygame.joystick.get_count()
  print('Joysticks: %i' % (n_joysticks,))

  if n_joysticks < 1:
    print('No joysticks found :(')
    return

  joystick = pygame.joystick.Joystick(0)
  joystick.init()

  print('Found: %s' % (joystick.get_name(),))

  print('Assuming an xbox controller. See top of file for details of change.')
  print('Use Back button to quit')

  state = {
      'roll': 0.0,
      'pitch': 0.0,
      'yaw': 0.0,
      'gas': 0.0,
      'take_off': False,
      'reset': False,
      'hover': False,
      };

  # Create a state timer
  STATE_TICK_EVENT = pygame.USEREVENT
  pygame.time.set_timer(STATE_TICK_EVENT, 50)

  while True:
    e = pygame.event.wait()
    if e.type == pygame.JOYBUTTONDOWN:
      if e.button == TAKE_OFF_BUTTON:
        state['take_off'] = True
      elif e.button == RESET_BUTTON:
        state['reset'] = True
      elif e.button == QUIT_BUTTON:
        print('Quitting')
        return
    elif e.type == pygame.JOYBUTTONUP:
      if e.button == TAKE_OFF_BUTTON:
        state['take_off'] = False
      elif e.button == RESET_BUTTON:
        state['reset'] = False
    elif e.type == pygame.JOYAXISMOTION:
      surface = None
      sign = 1.0

      if e.axis == ROLL_AXIS:
        surface = 'roll'
      elif e.axis == PITCH_AXIS:
        surface = 'pitch'
      elif e.axis == YAW_AXIS:
        surface = 'yaw'
      elif e.axis == GAS_AXIS:
        surface = 'gas'
        sign = -1.0
      elif e.axis == HOVER_AXIS:
        state['hover'] = value < -0.5

      if surface is not None:
        state[surface] = sign * e.value

    max_shift = 0.0
    for x in ('roll', 'pitch', 'yaw', 'gas'):
      max_shift = max(max_shift, abs(state[x]))
    
    #state['hover'] = max_shift < 0.3
    if state['hover']:
      state['gas'] = 0.0
    
    send_state(state)

if __name__ == '__main__':
  main()
