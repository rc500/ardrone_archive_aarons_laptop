#!/bin/sh

# Work out what directory this script is in and hence the build directory
this_dir_rel=`dirname $0`
this_dir=`readlink -f "${this_dir_rel}"`
build_dir="${this_dir}/build/native-mingw-win32"

toolchain_file=${this_dir}/mingw-toolchain.cmake
opencv_build_dir=${this_dir}/win32-third-party/opencv/build/

# Run cmake and copy (in this case) the pre-built libraries
pushd ${opencv_build_dir}
cmake "-DCMAKE_TOOLCHAIN_FILE=${toolchain_file}" .. "-DCMAKE_INSTALL_PREFIX=${this_dir}/ardrone/native" || die "Error configuring OpenCV"
make all install
popd

# Move into the build directory (creating it if necessary)
if [ ! -d "${build_dir}" ]; then
  mkdir -p "${build_dir}"
fi
pushd "${build_dir}"
cmake "-DCMAKE_TOOLCHAIN_FILE=${toolchain_file}" ../.. -DINSTALL_DOC=OFF "-DCMAKE_PREFIX_PATH=${opencv_build_dir}"
make all install
popd
