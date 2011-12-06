typedef struct p264_state_s p264_state_t;

p264_state_t* p264_open(void);
void p264_close(p264_state_t* s);
int p264_process_blockline(p264_state_t* s, char* buf, size_t buf_size);
char* p264_get_image_buffer(p264_state_t* s);
