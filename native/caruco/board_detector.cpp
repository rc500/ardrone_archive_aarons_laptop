#include "caruco.h"
#include "caruco_internal.hpp"
#include <iostream>

aruco_status_t aruco_detect_board(
    aruco_marker_vector_t*        detected_markers,
    aruco_board_configuration_t*  b_conf,
    aruco_board_t*                b_detected,
    aruco_camera_parameters_t*    cp,
    float                         marker_size_meters,
    float*                        lik)
{
  FUNC_BEGIN;
  aruco::BoardDetector d;
  *lik = d.detect(
      detected_markers->vector, b_conf->config, b_detected->board,
      cp->parameters, marker_size_meters);
  FUNC_END;
}
