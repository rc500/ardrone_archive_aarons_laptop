# Specify the project name, language and minimum CMake version required.
project(ardrone CXX)
cmake_minimum_required(VERSION 2.8)

# If we're building with GCC, switch on warnings
if(CMAKE_COMPILER_IS_GNUCC)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall")
endif(CMAKE_COMPILER_IS_GNUCC)

# If no default build is set, choose release with debug information
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "RelWithDebInfo")
endif(NOT CMAKE_BUILD_TYPE)

# We want to install to the ardrone/native directory relative to this ptoject.
set(CMAKE_INSTALL_PREFIX "${CMAKE_SOURCE_DIR}/ardrone/native")

# Build the libp264 library
add_subdirectory(third-party/libp264)

# Build the aruco library
#add_subdirectory(third-party/aruco-1.0.0)
