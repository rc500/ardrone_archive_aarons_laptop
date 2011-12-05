#include "caruco.h"
#include "caruco_internal.hpp"

using namespace aruco;

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

void aruco_marker_vector_push_back(aruco_marker_vector_t* v, aruco_marker_t* marker)
{
  v->vector.push_back(marker->marker);
}
