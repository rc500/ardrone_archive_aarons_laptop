#include "caruco.h"
#include "caruco_internal.hpp"

aruco_board_configuration_t* aruco_board_configuration_new()
{
  return new aruco_board_configuration_t();
}

void aruco_board_configuration_free(aruco_board_configuration_t* config)
{
  delete config;
}

void aruco_board_configuration_copy_from(
    aruco_board_configuration_t* config,
    aruco_board_configuration_t* other_config)
{
  config->config = other_config->config;
}

aruco_status_t aruco_board_configuration_save_to_file(
    aruco_board_configuration_t* config, const char* path)
{
  FUNC_BEGIN;
  config->config.saveToFile(path);
  FUNC_END;
}

aruco_status_t aruco_board_configuration_read_from_file(
    aruco_board_configuration_t* config, const char* path)
{
  FUNC_BEGIN;
  config->config.readFromFile(path);
  FUNC_END;
}

int aruco_board_configuration_marker_ids(
    aruco_board_configuration_t* config,
    int* ids)
{
  if(ids != NULL)
  {
    for(int r=0, i=0; r<config->config._markersId.rows; ++r)
      for(int c=0; c<config->config._markersId.cols; ++c, ++i)
      {
        ids[i] = config->config._markersId.at<int>(r, c);
      }
  }
  return config->config._markersId.cols * config->config._markersId.rows;
}
