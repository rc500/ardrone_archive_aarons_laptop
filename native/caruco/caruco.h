#ifndef CARUCO_H__
#define CARUCO_H__

#include <stdlib.h>
#include <stdint.h>
#include <aruco.h>

#ifdef __cplusplus
extern "C" {
#endif

/******* ENUMERATIONS *******/

/* funtions return ARUCO_FAILURE on failure and set error */
typedef enum {
  ARUCO_FAILURE = -1,
  ARUCO_SUCCESS = 0
} aruco_status_t;

/* boolean wrapper type */
typedef enum {
  ARUCO_FALSE = 0,
  ARUCO_TRUE = 1
} aruco_bool_t;

/******* STRUCTURES *******/

struct aruco_size_s {
  int                 width;
  int                 height;
};

struct aruco_image_s {
  /* A pointer to a packed RGB888 image of known width and height. It
   * is assumed that the stride is 3*width bytes. */
  uint8_t*            data;

  /* the size of the image */
  struct aruco_size_s size;
};

/******* OPAQUE HANDLE TYPES *******/

typedef struct aruco_board_s                aruco_board_t;
typedef struct aruco_board_detector_s       aruco_board_detector_t;
typedef struct aruco_board_configuration_s  aruco_board_configuration_t;
typedef struct aruco_camera_parameters_s    aruco_camera_parameters_t;
typedef struct aruco_marker_s               aruco_marker_t;
typedef struct aruco_marker_vector_s        aruco_marker_vector_t;

/******* ERROR HANDLING *******/

/* return description of last error */
const char* aruco_error_last_str();

/* return code for last error */
int         aruco_error_last_code();

/******* MARKER *******/

/* constructor/destructor */
aruco_marker_t* aruco_marker_new();
void            aruco_marker_free(aruco_marker_t* marker);

/* copy other_marker into marker */
void            aruco_marker_copy_from(
    aruco_marker_t* marker,
    aruco_marker_t* other_marker);

/* accessors */
aruco_bool_t aruco_marker_is_valid(aruco_marker_t* marker);
int aruco_marker_id(aruco_marker_t* marker);

/* calculate marker position and orientation relative to the camera */
aruco_status_t aruco_marker_calculate_extrinsics(
    aruco_marker_t*             marker,
    float                       marker_size, /* in meters */
    aruco_camera_parameters_t*  cp);

/* determine centroid of marker */
int aruco_marker_centroid_x(aruco_marker_t* marker);
int aruco_marker_centroid_y(aruco_marker_t* marker);

/* drawing a marker into an image */
void aruco_marker_draw(aruco_marker_t* marker,
    struct aruco_image_s* image,
    float r, float g, float b,
    int line_width /* =1 is a good default */,
    aruco_bool_t write_id);

void aruco_marker_draw_3d_axis(
    aruco_marker_t*             marker,
    struct aruco_image_s*       image,
    aruco_camera_parameters_t*  cp);

void aruco_marker_draw_3d_cube(
    aruco_marker_t*             marker,
    struct aruco_image_s*       image,
    aruco_camera_parameters_t*  cp);

/******* MARKER VECTOR *******/

/* constructor/destructor */
aruco_marker_vector_t*  aruco_marker_vector_new();
void                    aruco_marker_vector_free(
    aruco_marker_vector_t* marker_vector);

/* wrappers around std::vector<Marker> functionality */
void aruco_marker_vector_clear(aruco_marker_vector_t* v);
size_t aruco_marker_vector_size(aruco_marker_vector_t* v);
aruco_marker_t* aruco_marker_vector_element(aruco_marker_vector_t* v, size_t i);
void aruco_marker_vector_push_back(aruco_marker_vector_t* v, aruco_marker_t* marker);

/******* MARKER DETECTION *******/

/* simple detection with no extrinsic calculation */
aruco_status_t aruco_detect_markers(
    struct aruco_image_s*     input,
    aruco_marker_vector_t*    detected_markers /* output */);

/* Full detection. Only this function will result in marker extrinsics being
 * calculated. */
aruco_status_t aruco_detect_markers_full(
    struct aruco_image_s*       input,
    aruco_marker_vector_t*      detected_markers, /* output */
    aruco_camera_parameters_t*  cam_params,
    float                       marker_size_meters);

/******* CAMERA PARAMETERS *******/

/* constructor/destructor */
aruco_camera_parameters_t*  aruco_camera_parameters_new();
void                        aruco_camera_parameters_free(
    aruco_camera_parameters_t* parameters);

/* copy other_parameters into parameters */
void                        aruco_camera_parameters_copy_from(
    aruco_camera_parameters_t* parameters,
    aruco_camera_parameters_t* other_parameters);

/* accessors */
aruco_bool_t aruco_camera_parameters_is_valid(
    aruco_camera_parameters_t* parameters);

/* write the 9 coefficients of the camera matrix to the array passed. The coefficients
 * are written in C-style (i.e. row-major) ordering. */
void aruco_camera_parameters_get_camera_matrix(
    aruco_camera_parameters_t* parameters,
    float* m);

/* write the 4 distortion coefficients to m */
void aruco_camera_parameters_get_distortion_coeffs(
    aruco_camera_parameters_t* parameters,
    float* m);

/* file I/O */
aruco_status_t aruco_camera_parameters_save_to_file(
    aruco_camera_parameters_t* parameters, const char* path);
aruco_status_t aruco_camera_parameters_read_from_file(
    aruco_camera_parameters_t* parameters, const char* path);
aruco_status_t aruco_camera_parameters_read_from_xml_file(
    aruco_camera_parameters_t* parameters, const char* path);

/* mutators */
aruco_status_t aruco_camera_parameters_resize(
    aruco_camera_parameters_t* parameters,
    struct aruco_size_s* size);

/******* BOARD CONFIGURATION *******/

/* constructor/destructor */
aruco_board_configuration_t*  aruco_board_configuration_new();
void                          aruco_board_configuration_free(
    aruco_board_configuration_t* board_configuration);

/* copy other_config into config */
void                        aruco_board_configuration_copy_from(
    aruco_board_configuration_t* config,
    aruco_board_configuration_t* other_config);

/* accessors */
aruco_bool_t aruco_board_configuration_is_valid(
    aruco_board_configuration_t* config);

/* write ids to ids. Return number of ids in board configuration. Set ids=NULL
 * to query how many markers are in configuration. */
int aruco_board_configuration_marker_ids(
    aruco_board_configuration_t* config,
    int* ids);

/* file I/O */
aruco_status_t aruco_board_configuration_save_to_file(
    aruco_board_configuration_t* config, const char* path);
aruco_status_t aruco_board_configuration_read_from_file(
    aruco_board_configuration_t* config, const char* path);

/******* BOARD *******/

/* constructor/destructor */
aruco_board_t*  aruco_board_new();
void            aruco_board_free(aruco_board_t* board);

/* write the 3-element rotation vector (a Rodrigues rotation) and 3-element
 * translation vector to r and t. */
void aruco_board_get_extrinsics(aruco_board_t* board, float* r, float *t);

/* drawing*/

void aruco_board_draw_3d_axis(
    aruco_board_t*              board,
    struct aruco_image_s*       image,
    aruco_camera_parameters_t*  cp);

void aruco_board_draw_3d_cube(
    aruco_board_t*              board,
    struct aruco_image_s*       image,
    aruco_camera_parameters_t*  cp);

/******* BOARD DETECTOR *******/

aruco_status_t aruco_detect_board(
    aruco_marker_vector_t*        detected_markers, /* from aruco_marker_detector_detect */
    aruco_board_configuration_t*  b_conf, /* board to detect */
    aruco_board_t*                b_detected, /* output */
    aruco_camera_parameters_t*    cp,
    float                         marker_size_meters,
    float*                        lik /* output likelihood of detection */);

#ifdef __cplusplus
}
#endif

#endif // CARUCO_H__
