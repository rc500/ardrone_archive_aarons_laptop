#include "caruco.h"

#include <aruco.h>
#include <vector>

using namespace aruco;

struct aruco_marker_s { Marker marker; };
struct aruco_marker_vector_s { std::vector<Marker> vector; };
struct aruco_marker_dectector_s { MarkerDetector detector; };

namespace caruco {

static std::string last_error_str; int last_error_code;
void reset_error() { last_error_str = "No error"; last_error_code = 0; }
void set_error(const cv::Exception& e) { last_error_str = e.what(); last_error_code = e.code; }

}

using namespace caruco;

// utility macros to wrap up exception trapping
#define FUNC_BEGIN reset_error(); try {
#define FUNC_END } catch (cv::Exception& e__) {     \
  set_error(e__); return ARUCO_FAILURE;             \
}                                                   \
return ARUCO_SUCCESS;

// ERROR HANDLING
const char* aruco_error_last_str() { return caruco::last_error_str.c_str(); }
int aruco_error_last_code() { return caruco::last_error_code; }

// MARKER
aruco_marker_t* aruco_marker_new() { return new aruco_marker_s(); }
void aruco_marker_free(aruco_marker_t* marker) { delete marker; }

void aruco_marker_copy_from(aruco_marker_t* marker, aruco_marker_t* other_marker) {
  marker->marker = other_marker->marker;
}

aruco_bool_t aruco_marker_is_valid(aruco_marker_t* marker) {
  return marker->marker.isValid() ? ARUCO_TRUE : ARUCO_FALSE;
}

int aruco_marker_id(aruco_marker_t* marker) { return marker->marker.id; }

void aruco_marker_draw(aruco_marker_t* marker,
    uint8_t* image, uint32_t w, uint32_t h,
    float r, float g, float b,
    int line_width, aruco_bool_t write_id)
{
  // create a cv::Mat representing the input.
  int sizes[] = { w, h };
  cv::Mat input(2, sizes, CV_8UC3, image);
  marker->marker.draw(input, cv::Scalar(r,g,b), line_width, write_id == ARUCO_TRUE);
}

// MARKER VECTOR
aruco_marker_vector_t* aruco_marker_vector_new() { return new aruco_marker_vector_s(); }
void aruco_marker_vector_free(aruco_marker_vector_t* marker_vector) { delete marker_vector; }

void aruco_marker_vector_clear(aruco_marker_vector_t* v) { v->vector.clear(); }

size_t aruco_marker_vector_size(aruco_marker_vector_t* v) { return v->vector.size(); }

aruco_marker_t* aruco_marker_vector_element(aruco_marker_vector_t* v, size_t idx) {
  if(v->vector.empty())
    return NULL;
  if(idx >= v->vector.size())
    return NULL;
  return reinterpret_cast<aruco_marker_t*>(&(v->vector[idx]));
}

// MARKER DETECTION
aruco_marker_dectector_t* aruco_marker_detector_new() { return new aruco_marker_dectector_s(); }
void aruco_marker_detector_free(aruco_marker_dectector_t* detector) { delete detector; }

aruco_status_t aruco_marker_detector_detect(aruco_marker_dectector_t* d,
    uint8_t* image, uint32_t w, uint32_t h,
    aruco_marker_vector_t* markers)
{
  FUNC_BEGIN;

  // create a cv::Mat representing the input.
  int sizes[] = { w, h };
  cv::Mat input(2, sizes, CV_8UC3, image);

  // detect markers
  d->detector.detect(input, markers->vector, aruco::CameraParameters());

  FUNC_END;
}
