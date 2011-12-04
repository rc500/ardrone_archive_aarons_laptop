# The aruco headers need this
find_package(OpenCV REQUIRED)

add_library(caruco SHARED
  caruco.h
  caruco_internal.hpp

  error_handling.cpp

  board.cpp
  board_configuration.cpp
  board_detector.cpp
  camera_parameters.cpp
  marker.cpp
  marker_detector.cpp
  marker_vector.cpp
)
target_link_libraries(caruco aruco)

install(TARGETS caruco
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
)
