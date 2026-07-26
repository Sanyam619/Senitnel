#include "ab_api.h"
#include "ab_layout.h"

#include <stdlib.h>
#include <string.h>

#include "ab_internal.h"

ab_image *p4_open_image(const char *path) {
    ab_image *img = calloc(1, sizeof(*img));
    if (!img) return NULL;
    img->fp = fopen(path, "rb");
    if (!img->fp) { free(img); return NULL; }
    fseek(img->fp, 0, SEEK_END);
    long sz = ftell(img->fp);
    fseek(img->fp, 0, SEEK_SET);
    if (sz != AB_IMAGE_BYTES) { fclose(img->fp); free(img); return NULL; }
    img->len = (size_t)sz;
    img->map = malloc(img->len);
    if (!img->map) { fclose(img->fp); free(img); return NULL; }
    if (fread(img->map, 1, img->len, img->fp) != img->len) {
        fclose(img->fp); free(img->map); free(img); return NULL;
    }
    return img;
}

void p4_close_image(ab_image *img) {
    if (!img) return;
    if (img->fp) fclose(img->fp);
    free(img->map);
    free(img);
}
