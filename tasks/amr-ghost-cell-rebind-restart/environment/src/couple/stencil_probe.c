#include "couple.h"
#include <stdio.h>

int stencil_probe_dump(const face_buf_t *face, const char *path);

int stencil_probe_write(const face_buf_t *face, const char *path) {
    return stencil_probe_dump(face, path);
}
