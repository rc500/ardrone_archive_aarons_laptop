#include "caruco.h"
#include "caruco_internal.hpp"

aruco_board_t* aruco_board_new()
{
  return new aruco_board_t();
}

void aruco_board_free(aruco_board_t* board)
{
  delete board;
}

void aruco_board_draw_3d_axis(
    aruco_board_t* board,
    struct aruco_image_s* image,
    aruco_camera_parameters_t* cp)
{
  cv::Mat m(caruco::mat_from_image(image));
  aruco::CvDrawingUtils::draw3dAxis(m, board->board, cp->parameters);
}

void aruco_board_draw_3d_cube(
    aruco_board_t* board,
    struct aruco_image_s* image,
    aruco_camera_parameters_t* cp)
{
  cv::Mat m(caruco::mat_from_image(image));
  aruco::CvDrawingUtils::draw3dCube(m, board->board, cp->parameters);
}

void aruco_board_get_extrinsics(
    aruco_board_t* board,
    float* r, float *t)
{
  for(int i=0; i<3; ++i)
  {
    r[i] = board->board.Rvec.at<float>(i);
    t[i] = board->board.Tvec.at<float>(i);
  }
}
