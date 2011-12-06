#!/bin/sh

# Work out what directory this script is in and hence the build directory
this_dir=`dirname $0`
build_dir="${this_dir}/build/native-mingw-win32"

# Move into the build directory (creating it if necessary)
if [ ! -d "${build_dir}" ]; then
  mkdir -p "${build_dir}"
fi
cd "${build_dir}"

# Run cmake and make the librar{y,ies}.
cmake -DCMAKE_TOOLCHAIN_FILE=../../mingw-toolchain.cmake ../.. -DINSTALL_DIC=OFF
make all install

