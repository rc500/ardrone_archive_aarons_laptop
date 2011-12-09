from ardrone import aruco
import numpy as np
import cv2
import cv2.cv as cv

class Tracker(object):

  def __init__(self, cp_file, bc_files):
    self._marker_size = 0.1 #metres
    self.recon_pixel_size = 0.004 # metres

    recon_dim = (512, 256) # w, h

    self.boards = []
    for f in bc_files:
      print('Reading board config from: ' + f)
      config = aruco.BoardConfiguration()
      config.read_from_file(f)
      ids = config.marker_ids()
      recon_image = np.zeros((recon_dim[1],recon_dim[0],3))
      recon_mask = np.zeros((recon_dim[1],recon_dim[0],3))
      self.boards.append((config, ids, recon_image, recon_mask, [None, 0]))

    print('Reading camera parameters from: ' + cp_file)
    self._cam_param = aruco.CameraParameters()
    self._cam_param.read_from_xml_file(cp_file)
    self._cam_matrix = np.matrix(self._cam_param.get_camera_matrix())
    self._cam_distort = self._cam_param.get_distortion_coeffs()

  def recon_image(self, idx):
    if idx < 0 or idx >= len(self.boards):
      raise IndexError('No such board')
    recon_image = self.boards[idx][2]
    recon_mask = self.boards[idx][3]
    return np.array(recon_image / np.maximum(recon_mask, 1), dtype=np.uint8)

  def new_image(self, image):
    image = np.array(image)

    markers = aruco.detect_markers(image, self._cam_param, self._marker_size)

    # Did we find /any/ markers?
    if len(markers) == 0:
      return

    for config, ids, recon_image, recon_mask, detect in self.boards:
      # Filter markers
      m = [x for x in markers if x.id() in ids]

      # Skip boards not present
      if len(m) == 0:
        continue

      b, l = aruco.detect_board(m, config, self._cam_param, self._marker_size)
      detect[:] = (b,l)

      # Reject if we didn't find board
      if l < 0.1:
        continue

      # Get camera extrinsics
      rvec, tvec = [np.array(x) for x in b.get_extrinsics()]

      # Convert Rodrigues vector to rotation matrix
      R = np.zeros((3,3))
      cv2.Rodrigues(rvec, R)

      # Form the full homogenous projection matrix
      P = np.zeros((3,4))
      P[0:3,0:3] = R
      P[0:3,3] = tvec
      P = self._cam_matrix * np.matrix(P)
      
      Pext = np.zeros((4,4))
      Pext[0:3,:] = P
      Pext[3,3] = 1
      invP = np.linalg.inv(Pext)[0:3,:]
    
      h, w = recon_image.shape[0:2]
      midx = 0.5 * w
      midy = 0.5 * h

      imh, imw = image.shape[0:2]

      def plane_to_image(plane_point):
        x = np.matrix((
          (plane_point[0]-midx)*self.recon_pixel_size, 0, (plane_point[1]-midy)*self.recon_pixel_size, 1)
        ).transpose()
        xp = P * x
        xp = xp[0:2] / xp[2]
        return (xp[0,0], xp[1,0])

      # Source points are the corners of the recon image
      src_points = ((-midx,-midy), (midx,-midy), (midx,midy), (-midx,midy), (-midx,-midy))

      # Dest points in camera image
      dst_points = tuple([plane_to_image(x) for x in src_points])

      # Find transform from camera -> recon plane
      trans = cv.CreateMat(3, 3, cv.CV_32FC1)
      cv.GetPerspectiveTransform(dst_points, src_points, trans)
      trans = np.matrix(trans)

      # Boundary of image plane in recon plane
      bs = 5 # border size
      im_points = ((bs,bs), (imw-bs,bs), (imw-bs,imh-bs), (bs,imh-bs), (bs,bs))
      mask_points = [trans * np.matrix((x[0], x[1], 1)).transpose() for x in im_points]
      mask_points = [x[:-1] / x[-1] for x in mask_points]
      mask_points = np.array([(x[0,0], x[1,0]) for x in mask_points], dtype=np.int32)

      # Write the mask image
      mask = np.zeros(recon_mask.shape)
      cv2.fillConvexPoly(mask, mask_points, (1,1,1), lineType=cv2.CV_AA)
      recon_mask += mask

      #undist_image = cv2.undistort(np.array(image), self._cam_matrix, np.array(self._cam_distort))
      undist_image = np.array(image)

      recon=cv2.warpPerspective(undist_image, trans, (w,h))
      recon_image += recon * mask
