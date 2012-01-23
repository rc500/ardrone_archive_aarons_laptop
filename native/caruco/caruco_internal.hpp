#ifndef CARUCO_INTERNAL_H__
#define CARUCO_INTERNAL_H__

#include "caruco.h"

#include <aruco.h>
#include <vector>

// handle wrappers
struct aruco_board_s { aruco::Board board; };
struct aruco_board_configuration_s { aruco::BoardConfiguration config; };
struct aruco_camera_parameters_s { aruco::CameraParameters parameters; };
struct aruco_marker_s { aruco::Marker marker; };
struct aruco_marker_vector_s { std::vector<aruco::Marker> vector; };

// a namespace to hold functions/global variables private to caruco
namespace caruco {

  // FIXME: this error handling interface is not thread-safe. Mind you, neither
  // is errno on many platforms.
  extern std::string last_error_str;
  extern int last_error_code;

  inline void reset_error()
  {
    last_error_str = "No error"; last_error_code = 0;
  }

  inline void set_error(const cv::Exception& e)
  {
    last_error_str = e.err;
    last_error_code = e.code;
  }

  inline cv::Mat mat_from_image(struct aruco_image_s* image)
  {
    int sizes[] = { image->size.width, image->size.height };
    return cv::Mat(2, sizes, CV_8UC3, image->data);
  }

}

// utility macros to wrap up exception trapping
#define FUNC_BEGIN    caruco::reset_error();              \
                      try {
                        // ...function body goes here...
#define FUNC_END      } catch (cv::Exception& e__) {      \
                        caruco::set_error(e__);           \
                        return ARUCO_FAILURE;             \
                      }                                   \
                      return ARUCO_SUCCESS;

#endif // CARUCO_INTERNAL_H__
