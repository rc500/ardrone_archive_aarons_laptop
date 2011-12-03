#ifndef CARUCO_H__
#define CARUCO_H__

#include <stdlib.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/******* ENUMERATIONS *******/

/* funtions return ARUCO_FAILURE on failure and set error */
typedef enum { ARUCO_FAILURE = -1, ARUCO_SUCCESS = 0 } aruco_status_t;

/* boolean wrapper type */
typedef enum { ARUCO_FALSE = 0, ARUCO_TRUE = 1 } aruco_bool_t;

/******* STRUCTURES *******/

struct aruco_size_s {
  int width, height;
};

struct aruco_image_s {
  /* A pointer to a packed RGB888 image of known width and height. It
   * is assumed that the stride is 3*width bytes. */
  uint8_t*            data;

  /* the size of the image */
  struct aruco_size_s size;
};

/******* OPAQUE HANDLE TYPES *******/

typedef struct aruco_camera_parameters_s aruco_camera_parameters_t;
typedef struct aruco_marker_s aruco_marker_t;
typedef struct aruco_marker_detector_s aruco_marker_detector_t;
typedef struct aruco_marker_vector_s aruco_marker_vector_t;

/******* ERROR HANDLING *******/

/* return description of last error */
const char* aruco_error_last_str();

/* return code for last error */
int aruco_error_last_code();

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

/* drawing a marker into an image */
void aruco_marker_draw(aruco_marker_t* marker,
    struct aruco_image_s* image,
    float r, float g, float b,
    int line_width /* =1 is a good default */,
    aruco_bool_t write_id);

/******* MARKER VECTOR *******/

/* constructor/destructor */
aruco_marker_vector_t*  aruco_marker_vector_new();
void                    aruco_marker_vector_free(
    aruco_marker_vector_t* marker_vector);

/* wrappers around std::vector<Marker> functionality */
void aruco_marker_vector_clear(aruco_marker_vector_t* v);
size_t aruco_marker_vector_size(aruco_marker_vector_t* v);
aruco_marker_t* aruco_marker_vector_element(aruco_marker_vector_t* v, size_t i);

/******* MARKER DETECTION *******/

/* constructor/destructor */
aruco_marker_detector_t*  aruco_marker_detector_new();
void                      aruco_marker_detector_free(
    aruco_marker_detector_t* detector);

/* detecting markers */

/* simple detection with no extrinsic calculation */
aruco_status_t aruco_marker_detector_detect(
    aruco_marker_detector_t*  detector,
    struct aruco_image_s*     input,
    aruco_marker_vector_t*    detected_markers /* output */);

/* Full detection. Only this function will result in marker extrinsics being
 * calculated. */
aruco_status_t aruco_marker_detector_detect_full(
    aruco_marker_detector_t*    detector,
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

#ifdef __cplusplus
}
#endif

#endif // CARUCO_H__