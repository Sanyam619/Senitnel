#include "ab_layout.h"
#include "ab_policy.h"

#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int m3_finalize_region(const uint8_t *img, size_t len, uint8_t *work, int *live_slot,
                              char *action, size_t action_cap, int *bootable_a, int *bootable_b,
                              const ab_recovery_policy_t *policy);

static int hex_dump(const uint8_t *data, size_t len, char *out, size_t cap) {
    if (len * 2 + 1 > cap) return -1;
    for (size_t i = 0; i < len; i++) sprintf(out + i * 2, "%02x", data[i]);
    out[len * 2] = '\0';
    return 0;
}

static int process_case(const char *name, const char *data_root, const char *out_root,
                        const ab_recovery_policy_t *policy, FILE *report, int first) {
    char in_path[512];
    char out_path[512];
    snprintf(in_path, sizeof(in_path), "%s/%s.img", data_root, name);
    snprintf(out_path, sizeof(out_path), "%s/fixed_%s.img", out_root, name);

    FILE *fp = fopen(in_path, "rb");
    if (!fp) return 1;
    uint8_t img[AB_IMAGE_BYTES];
    if (fread(img, 1, sizeof(img), fp) != sizeof(img)) {
        fclose(fp);
        return 1;
    }
    fclose(fp);

    uint8_t work[AB_IMAGE_BYTES];
    int live_slot = 0;
    char action[32];
    int ba = 0, bb = 0;
    if (m3_finalize_region(img, sizeof(img), work, &live_slot, action, sizeof(action), &ba, &bb,
                           policy))
        return 1;

    FILE *outf = fopen(out_path, "wb");
    if (!outf) return 1;
    fwrite(work, 1, sizeof(work), outf);
    fclose(outf);

    char bl_hex[128 * 2 + 1];
    if (hex_dump(work + AB_BL0_SEC * AB_SECTOR_SIZE, 128, bl_hex, sizeof(bl_hex))) return 1;

    fprintf(report, "%s    \"%s\": {\n", first ? "" : ",\n", name);
    fprintf(report, "      \"live_slot\": \"%c\",\n", live_slot == 0 ? 'a' : 'b');
    fprintf(report, "      \"action\": \"%s\",\n", action);
    fprintf(report, "      \"bootable_slots\": [");
    int need_comma = 0;
    if (ba) {
        fprintf(report, "\"a\"");
        need_comma = 1;
    }
    if (bb) {
        fprintf(report, "%s\"b\"", need_comma ? ", " : "");
    }
    fprintf(report, "],\n");
    fprintf(report, "      \"bootloader_hex\": \"%s\"\n", bl_hex);
    fprintf(report, "    }");
    return 0;
}

static int ends_with_img(const char *name) {
    size_t n = strlen(name);
    return n > 4 && strcmp(name + n - 4, ".img") == 0;
}

static int basename_no_ext(const char *path, char *out, size_t cap) {
    const char *slash = strrchr(path, '/');
    const char *base = slash ? slash + 1 : path;
    size_t n = strlen(base);
    if (n <= 4 || n + 1 > cap) return -1;
    memcpy(out, base, n - 4);
    out[n - 4] = '\0';
    return 0;
}

int main(int argc, char **argv) {
    const char *policy_path = "/opt/abdev/config/active_policy.toml";
    const char *data_root = "/opt/abdev/data/scenarios";
    const char *out_root = "/output";
    const char *report_path = "/output/recovery.json";

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--policy") == 0 && i + 1 < argc) {
            policy_path = argv[++i];
        } else if (strcmp(argv[i], "--data") == 0 && i + 1 < argc) {
            data_root = argv[++i];
        } else if (strcmp(argv[i], "--out") == 0 && i + 1 < argc) {
            out_root = argv[++i];
        } else if (strcmp(argv[i], "--report") == 0 && i + 1 < argc) {
            report_path = argv[++i];
        } else {
            fprintf(stderr, "usage: recover --policy PATH --data DIR --out DIR --report PATH\n");
            return 2;
        }
    }

    ab_recovery_policy_t policy;
    if (ab_policy_load(policy_path, &policy)) {
        fprintf(stderr, "recover: failed to load policy %s\n", policy_path);
        return 1;
    }

    DIR *dir = opendir(data_root);
    if (!dir) {
        perror("opendir");
        return 1;
    }

    char names[32][128];
    int count = 0;
    struct dirent *ent;
    while ((ent = readdir(dir)) != NULL && count < 32) {
        if (!ends_with_img(ent->d_name)) continue;
        if (basename_no_ext(ent->d_name, names[count], sizeof(names[count]))) continue;
        count++;
    }
    closedir(dir);
    if (!count) {
        fprintf(stderr, "recover: no scenario images under %s\n", data_root);
        return 1;
    }

    for (int i = 0; i < count - 1; i++) {
        for (int j = i + 1; j < count; j++) {
            if (strcmp(names[i], names[j]) > 0) {
                char tmp[128];
                strcpy(tmp, names[i]);
                strcpy(names[i], names[j]);
                strcpy(names[j], tmp);
            }
        }
    }

    FILE *report = fopen(report_path, "w");
    if (!report) return 1;
    fprintf(report, "{\n  \"scenarios\": {\n");
    for (int i = 0; i < count; i++) {
        if (process_case(names[i], data_root, out_root, &policy, report, i == 0)) {
            fclose(report);
            return 1;
        }
    }
    fprintf(report, "\n  }\n}\n");
    fclose(report);
    return 0;
}
