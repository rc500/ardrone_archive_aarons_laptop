# The aruco headers need this
find_package(OpenCV REQUIRED)

add_library(caruco SHARED
  caruco.h
  caruco.cpp
)
target_link_libraries(caruco aruco)

install(TARGETS caruco
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
)
