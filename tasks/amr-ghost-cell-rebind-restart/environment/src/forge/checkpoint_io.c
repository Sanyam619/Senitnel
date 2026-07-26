#include "forge.h"
#include "ledger.h"
#include "mesh.h"
#include "couple.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BLOB_MAGIC 0x414d5246u

typedef struct {
    uint32_t gen_id;
    int block_tally;
    int tree_depth;
    int face_count;
    float mass_ref;
    float *faces;
} blob_view_t;

static int read_blob(const char *path, blob_view_t *out) {
    FILE *fp = fopen(path, "rb");
    if (!fp || !out) {
        return -1;
    }
    uint32_t magic = 0;
    if (fread(&magic, sizeof(magic), 1, fp) != 1 || magic != BLOB_MAGIC) {
        fclose(fp);
        return -1;
    }
    fread(&out->gen_id, sizeof(uint32_t), 1, fp);
    uint32_t blocks = 0;
    uint32_t depth = 0;
    uint32_t face_count = 0;
    fread(&blocks, sizeof(blocks), 1, fp);
    fread(&depth, sizeof(depth), 1, fp);
    fread(&face_count, sizeof(face_count), 1, fp);
    fread(&out->mass_ref, sizeof(float), 1, fp);
    out->block_tally = (int)blocks;
    out->tree_depth = (int)depth;
    out->face_count = (int)face_count;
    out->faces = calloc(face_count, sizeof(float));
    if (!out->faces) {
        fclose(fp);
        return -1;
    }
    fread(out->faces, sizeof(float), face_count, fp);
    fclose(fp);
    return 0;
}

static void free_blob(blob_view_t *b) {
    free(b->faces);
    b->faces = NULL;
}

static int load_fixture_meta(const char *path, float *mass_ref, int *face_count) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return -1;
    }
    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "mass_ref=", 9) == 0) {
            *mass_ref = strtof(line + 9, NULL);
        } else if (strncmp(line, "face_count=", 11) == 0) {
            *face_count = (int)strtol(line + 11, NULL, 10);
        }
    }
    fclose(fp);
    return 0;
}

static float face_l2(const float *a, const float *b, int n) {
    double acc = 0.0;
    for (int i = 0; i < n; i++) {
        double d = (double)a[i] - (double)b[i];
        acc += d * d;
    }
    return (float)sqrt(acc);
}

int forge_attach_fields(forge_ctx_t *ctx, mesh_ctx_t *mesh) {
    if (!ctx || !mesh) {
        return -1;
    }
    char blob_path[512];
    snprintf(blob_path, sizeof(blob_path), "/app/data/archive_cycle_%u.blob", ctx->gen_id);

    blob_view_t blob = {0};
    if (read_blob(blob_path, &blob) != 0) {
        return -1;
    }

    float mass_ref = 0.0f;
    int face_count = 0;
    load_fixture_meta(ctx->fixture_path, &mass_ref, &face_count);
    if (face_count <= 0 || face_count > blob.face_count) {
        face_count = blob.face_count;
    }

    face_buf_t face = {.values = blob.faces, .count = face_count};
    couple_fill_halo(&face, mesh->layout_ready, mesh->links_ready, mesh->link_gen);

    float ref_faces[64];
    char ref_path[512];
    snprintf(ref_path, sizeof(ref_path), "/app/data/ref_slices/%s_face.bin", ctx->scenario);
    FILE *rf = fopen(ref_path, "rb");
    if (!rf) {
        free_blob(&blob);
        return -1;
    }
    fread(ref_faces, sizeof(float), face_count, rf);
    fclose(rf);

    float base_l2 = face_l2(face.values, ref_faces, face_count);
    uint32_t tag = mesh_coupling_tag(mesh, ctx->gen_id, ctx->merge_target);
    couple_residual_metrics(tag, base_l2, &ctx->face_l2, &ctx->mass_drift);
    (void)mass_ref;
    ctx->block_tally = mesh->block_tally;
    ctx->tree_depth = mesh->tree_depth;
    free_blob(&blob);
    return 0;
}

int forge_load_generation_blob(uint32_t gen_id, blob_view_t *out) {
    char blob_path[512];
    snprintf(blob_path, sizeof(blob_path), "/app/data/archive_cycle_%u.blob", gen_id);
    return read_blob(blob_path, out);
}
