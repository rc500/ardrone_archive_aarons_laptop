#include <memory.h>
#include <stdlib.h>
#include <stdio.h>

#include <VLIB/video_codec.h>
#include <VLIB/video_controller.h>

#include <p264.h>

#define WIDTH 320
#define HEIGHT 240

#define FRAME_MODE_BUFFER_SIZE 25600

static video_stream_t stream;

struct p264_state_s
{
  video_controller_t* controller;
  vp_api_picture_t* picture;
  char* picturebuf;
};

char* p264_get_image_buffer(p264_state_t* s)
{
  return (char*)s->picture->y_buf;
}

p264_state_t* p264_open(void)
{
  p264_state_t* s = (p264_state_t*) calloc(1, sizeof(p264_state_t));
  s->controller = (video_controller_t*) calloc(1, sizeof(video_controller_t));
  s->picture = (vp_api_picture_t*) calloc(1, sizeof(vp_api_picture_t));

  s->picturebuf = (char*) calloc(1, WIDTH*HEIGHT*2);

  s->picture->format = PIX_FMT_RGB565;
  s->picture->framerate = 15;
  s->picture->width = WIDTH;
  s->picture->height = HEIGHT;
  s->picture->y_buf = (uint8_t*)s->picturebuf;
  s->picture->y_line_size = s->picture->width * 2;
  s->picture->cr_buf = calloc(1, WIDTH*HEIGHT*2);
  s->picture->cr_line_size = 0;
  s->picture->cb_buf = calloc(1, WIDTH*HEIGHT*2);
  s->picture->cb_line_size = 0;

  stream.bytes  = (uint32_t*)malloc(FRAME_MODE_BUFFER_SIZE*sizeof(uint32_t));
  stream.index  = 0;
  stream.used   = 0;
  stream.size   = FRAME_MODE_BUFFER_SIZE*sizeof(uint32_t);

  if(video_codec_open(s->controller, P264_CODEC))
  {
    printf("FAILED!\n");
    return NULL;
  }

  s->picture->vision_complete = 0;
  s->picture->complete = 0;
  s->picture->blockline = 0;

  video_controller_set_motion_estimation( s->controller, FALSE );
  video_controller_set_format( s->controller, WIDTH, HEIGHT );

  return s;
}

void p264_close(p264_state_t* s)
{
  if(s == NULL)
    return;

  video_codec_close(s->controller);
  free(s->controller);

  free(s);
}

#define DATA_RECEIVED_MAX_SIZE 8192

int p264_process_blockline(p264_state_t* s, char* buf, size_t buf_size)
{

  bool_t got_image;

  if(s == NULL)
    return 0;

  //printf("Got buffer at 0x%p size %lu. First byte: %i\n", buf, buf_size, (int)(buf[0]));

  got_image = FALSE;

#if 1
  //printf("Stream buffer: 0x%p\n", video_controller_get_stream_ptr(s->controller));
  //memcpy(video_controller_get_stream_ptr(s->controller), buf, buf_size);
  s->controller->in_stream.bytes   = (uint32_t*)(buf);
  s->controller->in_stream.used    = buf_size;
  s->controller->in_stream.size    = buf_size;
  s->controller->in_stream.index   = 0;
  s->controller->in_stream.length  = 32;
  s->controller->in_stream.code    = 0;

  //memset(s->picture->y_buf, 0, WIDTH*HEIGHT*2);
  //memcpy(s->picture->y_buf, buf, buf_size);
  //got_image = TRUE;

  video_decode_blockline(s->controller, s->picture, &got_image);
#else
  stream.index = 0;
  stream.used = buf_size;
  memcpy(&stream.bytes[0], (uint32_t*)buf, buf_size);
  video_decode_picture(s->controller, s->picture, &stream, &got_image );
#endif

  //printf("Picture width %u\n", s->picture->width);
  //printf("Got image: %i\n", got_image);
  //printf("Nframes: %i\n", s->controller->num_frames);

  //memset((char*)(s->picture->y_buf) + (WIDTH*HEIGHT), 0xff, WIDTH*HEIGHT);

  return got_image;
}
