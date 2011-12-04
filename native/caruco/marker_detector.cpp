#include "caruco.h"
#include "caruco_internal.hpp"

aruco_marker_detector_t* aruco_marker_detector_new()
{
  return new aruco_marker_detector_s();
}

void aruco_marker_detector_free(aruco_marker_detector_t* detector)
{
  delete detector;
}

aruco_status_t aruco_marker_detector_detect(
    aruco_marker_detector_t* d,
    struct aruco_image_s* image,
    aruco_marker_vector_t* markers)
{
  FUNC_BEGIN;
  cv::Mat m(caruco::mat_from_image(image));
  d->detector.detect(m, markers->vector, aruco::CameraParameters());
  FUNC_END;
}

aruco_status_t aruco_marker_detector_detect_full(
    aruco_marker_detector_t* d,
    struct aruco_image_s* image,
    aruco_marker_vector_t* markers,
    aruco_camera_parameters_t* cam_params,
    float marker_size_meters)
{
  FUNC_BEGIN;
  cv::Mat m(caruco::mat_from_image(image));
  d->detector.detect(m, markers->vector, cam_params->parameters,
      marker_size_meters);
  FUNC_END;
}
