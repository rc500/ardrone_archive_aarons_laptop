import experiments as e

def main():
  print('Loading logs...')

  # Change this to suit
  filename = '/data/rjw57/ardrone/logs/rjw57_office/rjw57_office_log.txt'

  log = e.load_drone_states_from_log(filename)
  frames = e.load_video_filenames_from_log(filename)
  e.gen_animation(frames, log)

if __name__ == '__main__':
  main()
