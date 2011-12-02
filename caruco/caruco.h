#ifndef CARUCO_H__
#define CARUCO_H__

#include <stdlib.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/******* UTILITY *******/

/* funtions return ARUCO_FAILURE on failure and set error */
typedef enum { ARUCO_FAILURE = -1, ARUCO_SUCCESS = 0 } aruco_status_t;

/* boolean wrapper type */
typedef enum { ARUCO_FALSE = 0, ARUCO_TRUE = 1 } aruco_bool_t;

/* error handling: return description of last error */
const char* aruco_error_last_str();

/* error handling: return code for last error */
int aruco_error_last_code();

/******* MARKER *******/

typedef struct aruco_marker_s aruco_marker_t;

/* constructor/destructor */
aruco_marker_t* aruco_marker_new();
void            aruco_marker_free(aruco_marker_t* marker);
void            aruco_marker_copy_from(aruco_marker_t* marker, aruco_marker_t* other_marker);

/* marker accessors */
aruco_bool_t aruco_marker_is_valid(aruco_marker_t* marker);
int aruco_marker_id(aruco_marker_t* marker);
void aruco_marker_draw(aruco_marker_t* marker,
    /* a pointer to a packed RGB888 image of width w and height h */
    uint8_t* image, uint32_t w, uint32_t h,
    float r, float g, float b,
    int line_width /* =1 is a good default */, aruco_bool_t write_id);

/******* MARKER VECTOR *******/

typedef struct aruco_marker_vector_s aruco_marker_vector_t;

/* constructor/destructor */
aruco_marker_vector_t*  aruco_marker_vector_new();
void                    aruco_marker_vector_free(aruco_marker_vector_t* marker_vector);

/* wrappers around std::vector<Marker> functionality */
void aruco_marker_vector_clear(aruco_marker_vector_t* v);
size_t aruco_marker_vector_size(aruco_marker_vector_t* v);
aruco_marker_t* aruco_marker_vector_element(aruco_marker_vector_t* v, size_t i);

/******* MARKER DETECTION *******/

typedef struct aruco_marker_dectector_s aruco_marker_dectector_t;

/* constructor/destructor */
aruco_marker_dectector_t* aruco_marker_detector_new();
void                      aruco_marker_detector_free(aruco_marker_dectector_t* detector);

/* detecting markers */

/* simple detection with no extrinsic calculation */
aruco_status_t aruco_marker_detector_detect(aruco_marker_dectector_t* detector,
    /* a pointer to a packed RGB888 image of width w and height h */
    uint8_t* image, uint32_t w, uint32_t h,
    
    /* output marker vector */
    aruco_marker_vector_t* markers);

#ifdef __cplusplus
}
#endif

#endif // CARUCO_H__
