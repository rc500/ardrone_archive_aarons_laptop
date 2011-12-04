#include "caruco.h"
#include "caruco_internal.hpp"

aruco_board_detector_t* aruco_board_detector_new()
{
  return new aruco_board_detector_t();
}

void aruco_board_detector_free(aruco_board_detector_t* board_detector)
{
  delete board_detector;
}

aruco_status_t aruco_board_detector_detect(
    aruco_board_detector_t*       detector,
    aruco_marker_vector_t*        detected_markers,
    aruco_board_configuration_t*  b_conf,
    aruco_board_t*                b_detected,
    aruco_camera_parameters_t*    cp,
    float                         marker_size_meters)
{
  FUNC_BEGIN;
  detector->detector.detect(
      detected_markers->vector, b_conf->config, b_detected->board,
      cp->parameters, marker_size_meters);
  FUNC_END;
}
