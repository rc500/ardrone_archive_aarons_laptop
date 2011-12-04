#include "caruco.h"
#include "caruco_internal.hpp"

namespace caruco
{
  std::string last_error_str;
  int last_error_code;
}

const char* aruco_error_last_str()
{
  return caruco::last_error_str.c_str();
}

int aruco_error_last_code()
{
  return caruco::last_error_code;
}
