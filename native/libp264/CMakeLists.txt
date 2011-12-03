project(libp264)
cmake_minimum_required(VERSION 2.8)

include_directories(${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/VP_Os/linux)

if(CMAKE_COMPILER_IS_GNUCC)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -O2 -g")
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -O2 -g")
endif(CMAKE_COMPILER_IS_GNUCC)

add_definitions(-DTARGET_CPU_X86=1)

if(UNIX)
  add_definitions(-DUSE_LINUX=1)
  if(CMAKE_COMPILER_IS_GNUCC)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")
  endif(CMAKE_COMPILER_IS_GNUCC)
endif(UNIX)

if(MINGW)
  add_definitions(-DUSE_MINGW32=1)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -mwindows")
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -mwindows")
endif(MINGW)

add_library(p264 SHARED
  libp264.c

  #VP_Api/vp_api.c
  VP_Api/vp_api_io_multi_stage.c
  #VP_Api/vp_api_supervisor.c
  VP_Api/vp_api_error.c
  #VP_Api/vp_api_stage.c
  #VP_Api/vp_api_thread_helper.c

  VP_Os/vp_os_malloc.c
  VP_Os/vp_os_error_handling.c

  VLIB/video_codec.c       VLIB/video_huffman.c     VLIB/video_packetizer.c
  VLIB/video_controller.c  VLIB/video_macroblock.c  VLIB/video_picture.c
  VLIB/video_dct.c         VLIB/video_mem32.c       VLIB/video_quantizer.c
  
  VLIB/Platform/x86/video_utils.c
  
  #VLIB/Stages/vlib_stage_decode.c
  #VLIB/Stages/vlib_stage_encode.c

  #VLIB/Utils/video_bin_dct.c

  VLIB/UVLC/uvlc.c
  VLIB/UVLC/uvlc_gob_layer.c
  VLIB/UVLC/uvlc_picture_layer.c
  VLIB/UVLC/uvlc_codec.c
  VLIB/UVLC/uvlc_mb_layer.c

  VLIB/Platform/x86/UVLC/uvlc_codec.c

  VLIB/P263/p263_codec.c
  VLIB/P263/p263_huffman.c
  VLIB/P263/p263_picture_layer.c
  VLIB/P263/p263_gob_layer.c
  VLIB/P263/p263_mb_layer.c

  VLIB/P264/p264.c                VLIB/P264/p264_inter_mc.c
  VLIB/P264/p264_merge.c          VLIB/P264/p264_transform.c
  VLIB/P264/p264_codec.c          VLIB/P264/p264_intra_pred.c
  VLIB/P264/p264_picture_layer.c  VLIB/P264/p264_zigzag.c
  VLIB/P264/p264_gob_layer.c      VLIB/P264/p264_mb_layer.c
  VLIB/P264/p264_Qp.c             VLIB/P264/video_p264.c
)

# Install the library
install(TARGETS p264
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
)
