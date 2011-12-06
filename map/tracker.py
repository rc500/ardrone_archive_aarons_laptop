from ardrone import aruco
import numpy as np
import cv2
import cv2.cv as cv

class Tracker(object):

  def __init__(self, bc_file, cp_file):
    self._marker_size = 0.06 #metres

    self._board_config = aruco.BoardConfiguration()
    self._board_config.read_from_file(bc_file)

    self._cam_param = aruco.CameraParameters()
    self._cam_param.read_from_xml_file(cp_file)
    self._cam_matrix = np.matrix(self._cam_param.get_camera_matrix())
    self._cam_distort = self._cam_param.get_distortion_coeffs()

    sq_size = (640, 480)
    self._recon_pixel_size = 0.002 # metres
    self._recon_image = np.zeros((sq_size[1],sq_size[0],3))
    self._recon_mask = np.zeros((sq_size[1],sq_size[0],3))

  def recon_image(self):
    return np.array(self._recon_image / np.maximum(self._recon_mask, 1), dtype=np.uint8)

  def new_image(self, image):
    image = np.array(image)

    m = aruco.detect_markers(image, self._cam_param, self._marker_size)
    if len(m) == 0:
      return

    b, l = aruco.detect_board(m, self._board_config, self._cam_param, self._marker_size)

    # Reject if we didn't find board
    if l < 0.1:
      return

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
  
    h, w = self._recon_image.shape[0:2]
    midx = 0.5 * w
    midy = 0.5 * h

    imh, imw = image.shape[0:2]

    def plane_to_image(plane_point):
      x = np.matrix((
        (plane_point[0]-midx)*self._recon_pixel_size, 0, (plane_point[1]-midy)*self._recon_pixel_size, 1)
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
    mask = np.zeros(self._recon_mask.shape)
    cv2.fillConvexPoly(mask, mask_points, (1,1,1), lineType=cv2.CV_AA)
    self._recon_mask += mask

    #undist_image = cv2.undistort(np.array(image), self._cam_matrix, np.array(self._cam_distort))
    undist_image = np.array(image)

    recon=cv2.warpPerspective(undist_image, trans, (w,h))
    self._recon_image += recon * mask
