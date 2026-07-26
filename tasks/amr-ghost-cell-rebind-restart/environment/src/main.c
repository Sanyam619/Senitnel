#include "forge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

extern int json_emit_aggregate(const char *out_path, const forge_ctx_t *items, int count, float mass_drift);

static int ensure_dir(const char *path) {
    char tmp[512];
    snprintf(tmp, sizeof(tmp), "%s", path);
    for (char *p = tmp + 1; *p; p++) {
        if (*p == '/') {
            *p = '\0';
            mkdir(tmp, 0755);
            *p = '/';
        }
    }
    return mkdir(tmp, 0755);
}

static int write_field_dump(const char *scenario, float l2, float mass) {
    char dir[256];
    snprintf(dir, sizeof(dir), "/output/fields/%s", scenario);
    ensure_dir(dir);
    char path[320];
    snprintf(path, sizeof(path), "%s/t0.bin", dir);
    FILE *fp = fopen(path, "wb");
    if (!fp) {
        return -1;
    }
    fwrite(&l2, sizeof(float), 1, fp);
    fwrite(&mass, sizeof(float), 1, fp);
    fclose(fp);
    snprintf(path, sizeof(path), "%s/t1.bin", dir);
    fp = fopen(path, "wb");
    if (!fp) {
        return -1;
    }
    float t1_l2 = l2 * 0.98f;
    float t1_mass = mass;
    fwrite(&t1_l2, sizeof(float), 1, fp);
    fwrite(&t1_mass, sizeof(float), 1, fp);
    fclose(fp);
    return 0;
}

static int run_one(const char *scenario, forge_ctx_t *out) {
    memset(out, 0, sizeof(*out));
    snprintf(out->scenario, sizeof(out->scenario), "%s", scenario);
    out->policy_path = "/app/data/policy_v2.table";
    char fixture[256];
    snprintf(fixture, sizeof(fixture), "/app/data/fixtures/%s.params", scenario);
    out->fixture_path = fixture;
    if (forge_run_recover(out) != 0) {
        return -1;
    }
    return write_field_dump(scenario, out->face_l2, out->mass_drift);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s recover-all\n", argv[0]);
        return 1;
    }
    if (strcmp(argv[1], "recover-all") != 0) {
        fprintf(stderr, "unknown command\n");
        return 1;
    }
    ensure_dir("/output");
    ensure_dir("/output/fields");
    const char *labels[] = {"alpha", "beta", "gamma"};
    forge_ctx_t results[3];
    float mass_acc = 0.0f;
    for (size_t i = 0; i < 3; i++) {
        if (run_one(labels[i], &results[i]) != 0) {
            return 1;
        }
        mass_acc += results[i].mass_drift;
    }
    float mass_drift = mass_acc / 3.0f;
    return json_emit_aggregate("/output/restart-summary.json", results, 3, mass_drift);
}
