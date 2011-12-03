#include "caruco.h"

#include <aruco.h>
#include <vector>

using namespace aruco;

// handle wrapper structures
struct aruco_camera_parameters_s { CameraParameters parameters; };
struct aruco_marker_s { Marker marker; };
struct aruco_marker_detector_s { MarkerDetector detector; };
struct aruco_marker_vector_s { std::vector<Marker> vector; };

// a namespace to hold functions/global variables private to caruco
namespace caruco {

  // FIXME: this error handling interface is not thread-safe. Mind you, neither
  // is errno on many platforms.
  static std::string last_error_str;
  int last_error_code;

  inline void reset_error()
  {
    last_error_str = "No error"; last_error_code = 0;
  }

  inline void set_error(const cv::Exception& e)
  {
    last_error_str = e.what();
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

// ERROR HANDLING
const char* aruco_error_last_str()
{
  return caruco::last_error_str.c_str();
}

int aruco_error_last_code()
{
  return caruco::last_error_code;
}

// MARKER
aruco_marker_t* aruco_marker_new()
{
  return new aruco_marker_s();
}

void aruco_marker_free(aruco_marker_t* marker)
{
  delete marker;
}

void aruco_marker_copy_from(aruco_marker_t* marker,
    aruco_marker_t* other_marker)
{
  marker->marker = other_marker->marker;
}

aruco_bool_t aruco_marker_is_valid(aruco_marker_t* marker)
{
  return marker->marker.isValid() ? ARUCO_TRUE : ARUCO_FALSE;
}

int aruco_marker_id(aruco_marker_t* marker)
{
  return marker->marker.id;
}

void aruco_marker_draw(aruco_marker_t* marker,
    struct aruco_image_s* image,
    float r, float g, float b,
    int line_width, aruco_bool_t write_id)
{
  cv::Mat m(caruco::mat_from_image(image));
  marker->marker.draw(m, cv::Scalar(r,g,b), line_width, write_id == ARUCO_TRUE);
}

// MARKER VECTOR
aruco_marker_vector_t* aruco_marker_vector_new()
{
  return new aruco_marker_vector_s();
}

void aruco_marker_vector_free(aruco_marker_vector_t* marker_vector)
{
  delete marker_vector;
}

void aruco_marker_vector_clear(aruco_marker_vector_t* v)
{
  v->vector.clear();
}

size_t aruco_marker_vector_size(aruco_marker_vector_t* v)
{
  return v->vector.size();
}

aruco_status_t aruco_marker_calculate_extrinsics(
    aruco_marker_t*             m,
    float                       marker_size,
    aruco_camera_parameters_t*  cp)
{
  FUNC_BEGIN;
  m->marker.calculateExtrinsics(marker_size, cp->parameters);
  FUNC_END;
}

aruco_marker_t* aruco_marker_vector_element(aruco_marker_vector_t* v, size_t idx)
{
  if(v->vector.empty())
    return NULL;
  if(idx >= v->vector.size())
    return NULL;
  return reinterpret_cast<aruco_marker_t*>(&(v->vector[idx]));
}

// MARKER DETECTION
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

// CAMERA PARAMETERS
aruco_camera_parameters_t* aruco_camera_parameters_new()
{
  return new aruco_camera_parameters_s();
}

void aruco_camera_parameters_free(aruco_camera_parameters_t* camera_parameters)
{
  delete camera_parameters;
}

void aruco_camera_parameters_copy_from(
    aruco_camera_parameters_t* p,
    aruco_camera_parameters_t* other_p)
{
  p->parameters = other_p->parameters;
}

aruco_bool_t aruco_camera_parameters_is_valid(
    aruco_camera_parameters_t* p)
{
  return p->parameters.isValid() ? ARUCO_TRUE : ARUCO_FALSE;
}

aruco_status_t aruco_camera_parameters_read_from_file(
    aruco_camera_parameters_t* p,
    const char* path)
{
  FUNC_BEGIN;
  p->parameters.readFromFile(path);
  FUNC_END;
}

aruco_status_t aruco_camera_parameters_read_from_xml_file(
    aruco_camera_parameters_t* p,
    const char* path)
{
  FUNC_BEGIN;
  p->parameters.readFromXMLFile(path);
  FUNC_END;
}

aruco_status_t aruco_camera_parameters_resize(
    aruco_camera_parameters_t* p,
    struct aruco_size_s* s)
{
  FUNC_BEGIN;
  p->parameters.resize(cv::Size(s->width, s->height));
  FUNC_END;
}

aruco_status_t aruco_camera_parameters_save_to_file(
    aruco_camera_parameters_t* p,
    const char* path)
{
  FUNC_BEGIN;
  p->parameters.saveToFile(path);
  FUNC_END;
}
