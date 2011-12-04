#include "caruco.h"
#include "caruco_internal.hpp"

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
