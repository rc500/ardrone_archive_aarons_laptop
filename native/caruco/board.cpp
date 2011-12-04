#include "caruco.h"
#include "caruco_internal.hpp"

aruco_board_t* aruco_board_new()
{
  return new aruco_board_t();
}

void aruco_board_free(aruco_board_t* board)
{
  delete board;
}
