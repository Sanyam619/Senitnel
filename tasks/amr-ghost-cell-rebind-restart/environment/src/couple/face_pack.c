#include "couple.h"

int couple_pack_faces(const float *src, int count, face_buf_t *out);

int face_pack_linear(const float *src, int n, face_buf_t *out) {
    return couple_pack_faces(src, n, out);
}
