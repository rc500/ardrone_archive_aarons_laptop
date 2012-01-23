#!/bin/sh

# Work out what directory this script is in and hence the build directory
this_dir_rel=`dirname $0`
this_dir=`readlink -f "${this_dir_rel}"`
build_dir="${this_dir}/build/native-linux"

# Move into the build directory (creating it if necessary)
if [ ! -d "${build_dir}" ]; then
  mkdir -p "${build_dir}"
fi
cd "${build_dir}"

# Run cmake and make the librar{y,ies}.
cmake ../../native -DINSTALL_DOC=ON "-DCMAKE_INSTALL_PREFIX=${this_dir}/ardrone/native"
make doc
make all install

