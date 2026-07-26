#include "forge.h"
#include <stdio.h>
#include <string.h>

int json_emit_summary(const forge_ctx_t *ctx, float mass_drift, const char *out_path) {
    FILE *fp = fopen(out_path, "w");
    if (!fp || !ctx) {
        return -1;
    }
    fprintf(fp,
            "{\n"
            "  \"schema_tag\": \"" RESTART_JSON_TAG "\",\n"
            "  \"scenarios\": [\n"
            "    {\"label\": \"%s\", \"block_tally\": %d, \"face_l2\": %.8f}\n"
            "  ],\n"
            "  \"mass_drift\": %.8f,\n"
            "  \"tree_depth\": %d\n"
            "}\n",
            ctx->scenario, ctx->block_tally, ctx->face_l2, mass_drift, ctx->tree_depth);
    fclose(fp);
    return 0;
}

int json_emit_aggregate(const char *out_path, const forge_ctx_t *items, int count, float mass_drift) {
    FILE *fp = fopen(out_path, "w");
    if (!fp || !items || count <= 0) {
        return -1;
    }
    fprintf(fp, "{\n  \"schema_tag\": \"" RESTART_JSON_TAG "\",\n  \"scenarios\": [\n");
    for (int i = 0; i < count; i++) {
        fprintf(fp,
                "    {\"label\": \"%s\", \"block_tally\": %d, \"face_l2\": %.8f}%s\n",
                items[i].scenario, items[i].block_tally, items[i].face_l2,
                (i + 1 < count) ? "," : "");
    }
    int depth = items[0].tree_depth;
    for (int i = 1; i < count; i++) {
        if (items[i].tree_depth > depth) {
            depth = items[i].tree_depth;
        }
    }
    fprintf(fp, "  ],\n  \"mass_drift\": %.8f,\n  \"tree_depth\": %d\n}\n", mass_drift, depth);
    fclose(fp);
    return 0;
}
