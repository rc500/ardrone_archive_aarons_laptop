import json, socket, time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

seq = 0
def send_state(state):
  global seq, sock
  seq += 1
  HOST, PORT = ('127.0.0.1', 5560)
  print('state is', json.dumps({'seq': seq, 'state': state}))
  sock.sendto(json.dumps({'seq': seq, 'state': state}), (HOST, PORT))

def main():
	print('Hello')
	state = {
		'roll': 0.0,
		'pitch': 0.0,
		'yaw': 0.0,
		'gas': 0.0,
		'take_off': False,
		'reset': False,
		'hover': True,
	      };

	state['reset'] = True
	send_state(state)

	time.sleep(0.5)

	state['reset'] = False
	send_state(state)

	time.sleep(5)

	state['take_off'] = True
	send_state(state)

	time.sleep(0.5)

	state['take_off'] = False
	send_state(state)

	time.sleep(10)

	state['take_off'] = True
	send_state(state)

	time.sleep(0.5)

	state['take_off'] = False
	send_state(state)


if __name__ == '__main__':
  main()
