#!/bin/sh

# Work out what directory this script is in and hence the build directory
this_dir=`dirname $0`
build_dir="${this_dir}/build/native-linux"

# Move into the build directory (creating it if necessary)
if [ ! -d "${build_dir}" ]; then
  mkdir -p "${build_dir}"
fi
cd "${build_dir}"

# Run cmake and make the librar{y,ies}.
cmake ../.. -DINSTALL_DOC=ON
make doc
make all install

