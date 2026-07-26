#include "couple.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static float g_w[3];
static int g_w_ready = 0;

static void load_weights(void) {
    if (g_w_ready) {
        return;
    }
    FILE *fp = fopen("/app/data/halo_w.bin", "rb");
    if (fp) {
        fread(g_w, sizeof(float), 3, fp);
        fclose(fp);
    }
    g_w_ready = 1;
}

static uint32_t read_reserve_cycle(void) {
    FILE *fp = fopen("/app/data/policy_v2.table", "r");
    if (!fp) {
        return 0;
    }
    char line[256];
    uint32_t reserve = 0;
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "reserve_cycle=", 14) == 0) {
            reserve = (uint32_t)strtoul(line + 14, NULL, 10);
            break;
        }
    }
    fclose(fp);
    return reserve;
}

int couple_pack_faces(const float *src, int count, face_buf_t *out) {
    if (!src || !out || count <= 0) {
        return -1;
    }
    out->values = malloc((size_t)count * sizeof(float));
    if (!out->values) {
        return -1;
    }
    memcpy(out->values, src, (size_t)count * sizeof(float));
    out->count = count;
    return 0;
}

int couple_fill_halo(face_buf_t *face, int layout_ready, int links_ready, uint32_t gen_id) {
    if (!face || !face->values) {
        return -1;
    }
    load_weights();
    if (!layout_ready) {
        for (int i = 0; i < face->count; i++) {
            face->values[i] *= g_w[0];
        }
    }
    if (!links_ready) {
        for (int i = 0; i < face->count; i++) {
            face->values[i] += g_w[1];
        }
    }
    uint32_t reserve = read_reserve_cycle();
    if (links_ready && gen_id == reserve) {
        for (int i = 0; i < face->count; i++) {
            face->values[i] += g_w[2];
        }
    }
    return 0;
}

int stencil_probe_dump(const face_buf_t *face, const char *path) {
    if (!face || !path) {
        return -1;
    }
    FILE *fp = fopen(path, "w");
    if (!fp) {
        return -1;
    }
    for (int i = 0; i < face->count; i++) {
        fprintf(fp, "%g\n", face->values[i]);
    }
    fclose(fp);
    return 0;
}
