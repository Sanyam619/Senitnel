#include "common.h"
#include "gate.h"
#include "health.h"
#include "reload.h"
#include "vault.h"
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int json_emit_ledger(const char *path, const struct case_out *cases, int n, uint32_t reload_epoch);

static int parse_case(const char *path, struct case_in *out) {
    FILE *fp = fopen(path, "r");
    char line[MAX_LINE];
    if (!fp || !out) {
        if (fp) {
            fclose(fp);
        }
        return -1;
    }
    memset(out, 0, sizeof(*out));
    while (fgets(line, sizeof(line), fp)) {
        char *nl = strchr(line, '\n');
        if (nl) {
            *nl = '\0';
        }
        if (strncmp(line, "id=", 3) == 0) {
            snprintf(out->id, sizeof(out->id), "%s", line + 3);
        } else if (strncmp(line, "store_gen=", 10) == 0) {
            out->store_gen = (uint32_t)strtoul(line + 10, NULL, 10);
        } else if (strncmp(line, "subject_lin=", 12) == 0) {
            snprintf(out->subject_lin, sizeof(out->subject_lin), "%s", line + 12);
        } else if (strncmp(line, "claim_lin=", 10) == 0) {
            snprintf(out->claim_lin, sizeof(out->claim_lin), "%s", line + 10);
        } else if (strncmp(line, "tok_id=", 7) == 0) {
            snprintf(out->tok_id, sizeof(out->tok_id), "%s", line + 7);
        } else if (strncmp(line, "cached_ok=", 10) == 0) {
            out->cached_ok = (int)strtol(line + 10, NULL, 10);
        } else if (strncmp(line, "refresh=", 8) == 0) {
            out->refresh = (int)strtol(line + 8, NULL, 10);
        }
    }
    fclose(fp);
    return out->id[0] ? 0 : -1;
}

static int cmp_id(const void *a, const void *b) {
    const struct case_out *ca = a;
    const struct case_out *cb = b;
    return strcmp(ca->id, cb->id);
}

static int run_admit(const char *out_path) {
    DIR *d = opendir("/app/data/scenarios");
    struct dirent *ent;
    struct case_in ins[MAX_CASES];
    struct case_out outs[MAX_CASES];
    int n = 0;
    uint32_t reload_epoch = 0;
    struct slot_a sa;

    if (!d) {
        return 1;
    }
    while ((ent = readdir(d)) != NULL && n < MAX_CASES) {
        char path[512];
        size_t len;
        if (ent->d_name[0] == '.') {
            continue;
        }
        len = strlen(ent->d_name);
        if (len < 5 || strcmp(ent->d_name + len - 5, ".case") != 0) {
            continue;
        }
        snprintf(path, sizeof(path), "/app/data/scenarios/%s", ent->d_name);
        if (parse_case(path, &ins[n]) != 0) {
            closedir(d);
            return 1;
        }
        if (assemble_x(&ins[n], &outs[n]) != 0) {
            closedir(d);
            return 1;
        }
        if (assemble_y(&ins[n], &outs[n]) != 0) {
            closedir(d);
            return 1;
        }
        n++;
    }
    closedir(d);
    if (n == 0) {
        return 1;
    }
    qsort(outs, (size_t)n, sizeof(outs[0]), cmp_id);
    if (slot_read_a(ins[0].id, &sa) != 0) {
        return 1;
    }
    reload_epoch = sa.bound_gen;
    if (json_emit_ledger(out_path, outs, n, reload_epoch) != 0) {
        return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "surf") == 0) {
        return surf_tls();
    }
    if (argc >= 2 && strcmp(argv[1], "reload") == 0) {
        return apply_snap() == 0 ? 0 : 1;
    }
    if (argc >= 3 && strcmp(argv[1], "admit") == 0) {
        return run_admit(argv[2]);
    }
    fprintf(stderr, "usage: edgegate admit <out>|surf|reload\n");
    return 2;
}
