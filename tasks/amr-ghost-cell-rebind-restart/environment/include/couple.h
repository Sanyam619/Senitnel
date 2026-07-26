#ifndef COUPLE_H
#define COUPLE_H

#include <stdint.h>

typedef struct {
    float *values;
    int count;
} face_buf_t;

int couple_pack_faces(const float *src, int count, face_buf_t *out);
int couple_fill_halo(face_buf_t *face, int layout_ready, int links_ready, uint32_t gen_id);
void couple_residual_metrics(uint32_t tag, float base, float *l2, float *mass);
int stencil_probe_dump(const face_buf_t *face, const char *path);

#endif
