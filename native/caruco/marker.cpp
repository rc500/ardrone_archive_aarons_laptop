#include "caruco.h"
#include "caruco_internal.hpp"

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

int aruco_marker_centroid_x(
    aruco_marker_t* marker)
{
  return marker->marker.centroid_x();
}

int aruco_marker_centroid_y(
    aruco_marker_t* marker)
{
  return marker->marker.centroid_y();
}

void aruco_marker_draw(aruco_marker_t* marker,
    struct aruco_image_s* image,
    float r, float g, float b,
    int line_width, aruco_bool_t write_id)
{
  cv::Mat m(caruco::mat_from_image(image));
  marker->marker.draw(m, cv::Scalar(r,g,b), line_width, write_id == ARUCO_TRUE);
}

void aruco_marker_draw_3d_axis(
    aruco_marker_t* marker,
    struct aruco_image_s* image,
    aruco_camera_parameters_t* cp)
{
  cv::Mat m(caruco::mat_from_image(image));
  aruco::CvDrawingUtils::draw3dAxis(m, marker->marker, cp->parameters);
}

void aruco_marker_draw_3d_cube(
    aruco_marker_t* marker,
    struct aruco_image_s* image,
    aruco_camera_parameters_t* cp)
{
  cv::Mat m(caruco::mat_from_image(image));
  aruco::CvDrawingUtils::draw3dCube(m, marker->marker, cp->parameters);
}
