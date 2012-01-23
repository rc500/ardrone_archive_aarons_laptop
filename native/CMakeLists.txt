# Specify the project name, language and minimum CMake version required.
project(ardrone CXX)
cmake_minimum_required(VERSION 2.8)

# If we're building with GCC, switch on warnings
if(CMAKE_COMPILER_IS_GNUCC)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall")
endif(CMAKE_COMPILER_IS_GNUCC)

if("${CMAKE_SYSTEM_PROCESSOR}" STREQUAL "x86_64")
  set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -fPIC"  )
  set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_DEBUG} -fPIC"  )
endif("${CMAKE_SYSTEM_PROCESSOR}" STREQUAL "x86_64")

# If no default build is set, choose release with debug information
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "RelWithDebInfo")
endif(NOT CMAKE_BUILD_TYPE)

# The following makes sure that an rpath is set in Linux luibraries so
# dependencies can be found.
set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# Build the aruco library
add_subdirectory(third-party/aruco-1.0.0)
include_directories("${CMAKE_SOURCE_DIR}/third-party/aruco-1.0.0/src")

# Build the native libraries
add_subdirectory(libp264)
add_subdirectory(caruco)
