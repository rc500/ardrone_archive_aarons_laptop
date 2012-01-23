#include "caruco.h"
#include "caruco_internal.hpp"

aruco_status_t aruco_detect_markers(
    struct aruco_image_s* image,
    aruco_marker_vector_t* markers)
{
  FUNC_BEGIN;
  aruco::MarkerDetector d;
  cv::Mat m(caruco::mat_from_image(image));
  d.detect(m, markers->vector, aruco::CameraParameters());
  FUNC_END;
}

aruco_status_t aruco_detect_markers_full(
    struct aruco_image_s* image,
    aruco_marker_vector_t* markers,
    aruco_camera_parameters_t* cam_params,
    float marker_size_meters)
{
  FUNC_BEGIN;
  aruco::MarkerDetector d;
  cv::Mat m(caruco::mat_from_image(image));
  d.detect(m, markers->vector, cam_params->parameters,
      marker_size_meters);
  FUNC_END;
}
