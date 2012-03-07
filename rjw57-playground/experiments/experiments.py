import json, os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.image as mpimg
import matplotlib.animation as mpanim

def load_log(filename=None):
  if filename is None:
    filename = '/data/rjw57/ardrone/logs/rjw57_office/rjw57_office_log.txt'

  log = []
  with open(filename) as log_file:
    for l in log_file:
      log.append(json.loads(l))

  return log

def load_drone_states_from_log(filename=None):
  """Return an array where each row is one record from the log. Each row records:

  * 0,  The time (in seconds) of the data capture
  * 1,  The theta orientation angle in radians
  * 2,  The phi orientation angle in radians
  * 3,  The psi orientation angle in radians
  * 4,  The altitude from the altimeter in millimetres
  * 5,  The linear x velocity in millimetres/second (guessed units)
  * 6,  The linear y velocity in millimetres/second (guessed units)
  * 7,  The linear z velocity in millimetres/second (guessed units)
  * 8,  The (absolute) change in theta since the last frame in radians
  * 9,  The (absolute) change in phi since the last frame in radians
  * 10, The (absolute) change in psi since the last frame in radians
  * 11, The time (in seconds) of this log message which can be used to synchronise with a video frame

  """
  
  if filename is None:
    filename = '/data/rjw57/ardrone/logs/rjw57_office/rjw57_office_log.txt'

  log = []
  last_stamp = None
  with open(filename) as log_file:
    for l in log_file:
      record = json.loads(l)
      if record['type'] == 'state_from_drone' and record['what']['type'] == 'vision':
        vision = record['what']

        capture_stamp = vision['time_capture']

        # Skip duplicate records
        if last_stamp is not None and last_stamp == capture_stamp:
          continue
        last_stamp = capture_stamp

        capture_seconds = capture_stamp >> 21
        capture_useconds = capture_stamp & ((1<<21) - 1)
        capture_time = (1e-6 * capture_useconds) + capture_seconds

        log.append([
          capture_time,
          vision['theta_capture'], vision['phi_capture'], vision['psi_capture'], vision['altitude_capture'],
          vision['body_v']['x'], vision['body_v']['y'], vision['body_v']['z'],
          vision['delta_theta'], vision['delta_phi'], vision['delta_psi'],
          record['when']
          ])

  return np.array(log)

def load_video_filenames_from_log(filename=None):
  """Return a list of (timestamp, filename) pairs for the video filenames."""
  
  if filename is None:
    filename = '/data/rjw57/ardrone/logs/rjw57_office/rjw57_office_log.txt'

  file_base = os.path.dirname(filename)

  log = []
  last_stamp = None
  with open(filename) as log_file:
    for l in log_file:
      record = json.loads(l)
      if record['type'] == 'frame_from_drone':
        log.append((record['when'], os.path.join(file_base, record['what'])))

  return log

def gen_animation(frames, log):
  fig = plt.figure()

  state = {'start_hint': 0}
  fps = len(frames) / (frames[-1][0] - frames[0][0])

  def anim_func(frame_index, state):
    print('Frame %i/%i' % (1+frame_index, len(frames)))
    fig.set_dpi(100)
    fig.set_figwidth(1280.0/fig.get_dpi())
    fig.set_figheight(720.0/fig.get_dpi())
    state['start_hint'] = plot_video_frame(frames, log, frame_index, start_hint=state['start_hint'], fig=fig)

  anim = mpanim.FuncAnimation(fig, anim_func, range(len(frames)), init_func=fig.clear, fargs=(state,))
  anim.save('anim.mp4', fps=fps, clear_temp=False, frame_prefix='gen_anim_temp_')

def plot_video_frame(frames, log, frame_idx, start_hint=0, png_file=None, fig=None):
  frame_when, frame_file = frames[frame_idx]

  idx = start_hint
  while idx < len(log) and log[idx, 11] < frame_when:
    idx += 1

  if idx >= len(log):
    raise IndexError('frame is beyond end of log')

  im = mpimg.imread(frame_file)

  if fig is None:
    fig = plt.figure()

  fig.clear()
  ax = fig.add_axes([0, 0, 0.8, 1], projection='3d')
  plot_path(log, ax=ax, highlight_idx=idx)

  ax2 = fig.add_axes([0.725, 0.35, 0.3, 0.3])
  ax2.axison = False
  plt.imshow(im, axes=ax2, origin='lower', aspect='equal')
  plt.draw()

  if png_file is not None:
    plt.savefig(png_file)

  return idx

def plot_path(log, ax=None, highlight_idx=None):
  """Pass this a log array as provided by load_drone_states_from_log()."""

  if ax is None:
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

  delta_t = np.diff(log[:,0])
  x = np.cumsum(log[:-1,5] * delta_t)
  y = np.cumsum(log[:-1,6] * delta_t)
  #z = np.cumsum(log[:-1,7] * delta_t)
  z = log[:-1,4]
  ax.plot(x, y, z)

  if highlight_idx is not None:
    hx = [x[highlight_idx],]
    hy = [y[highlight_idx],]
    hz = [z[highlight_idx],]
    ax.plot(hx, hy , hz, 'r.', ms=10)

