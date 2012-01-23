import logging
logging.basicConfig(level = logging.DEBUG)

import os
import sys
import numpy as np
from PIL import Image
import cv2 as cv

# Where is this file?
this_dir = os.path.abspath(os.path.dirname(__file__))

# Insert a path to load modules from relative to this file
sys.path.insert(0, os.path.abspath(os.path.join(this_dir, '..')))

# Load the aruco module.
import ardrone.aruco as aruco

def main():
  """The main entry point of the program."""

  # Check the command-line arcuments.
  if len(sys.argv) < 5:
    print('usage: aruco.py input.png camera_params.yml board_config.abc output.png')
    sys.exit(1)

  # Load input
  input_image = Image.open(sys.argv[1]).convert('RGB')

  # Load camera calibration
  cam_params = aruco.CameraParameters()
  cam_params.read_from_xml_file(sys.argv[2])

  # Load board config
  board_config = aruco.BoardConfiguration()
  board_config.read_from_file(sys.argv[3])

  # Detect board
  marker_size = 0.06
  markers = aruco.detect_markers(input_image, cam_params, marker_size)
  board, lik = aruco.detect_board(markers, board_config, cam_params, marker_size)

  arr = np.array(input_image)

  # Draw markers
  [m.draw(arr, (1,0,0), write_id=False) for m in markers]
  [m.draw_3d_cube(arr, cam_params) for m in markers]

  # Draw board axis
  board.draw_3d_axis(arr, cam_params)

  Image.fromarray(arr).save(sys.argv[4], 'PNG')

if __name__ == '__main__':
  main()
