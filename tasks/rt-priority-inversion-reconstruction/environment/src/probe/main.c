#include "klb_types.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int stage_a(const char *trace, KlbWeave *w, KlbLatch *l, char missed[32]);
int stage_b(const char *cfg, const KlbLatch *l, const char *missed, char chain[3][32], int *ceilings, int *n_ceil);

static void write_json(FILE *out, const char *sid, const char *missed, char chain[3][32], int *ceilings, int n_ceil, const char *gates[], int n_gate) {
    fprintf(out, "    \"%s\": {\n", sid);
    fprintf(out, "      \"missed_deadline_task\": \"%s\",\n", missed);
    fprintf(out, "      \"chain\": [\"%s\", \"%s\", \"%s\"],\n", chain[0], chain[1], chain[2]);
    fprintf(out, "      \"ceilings\": {");
    for (int i = 0; i < n_gate; i++) {
        int v = (i < n_ceil) ? ceilings[i] : 0;
        fprintf(out, "%s\"%s\": %d", i ? ", " : "", gates[i], v);
    }
    fprintf(out, "}\n    }");
}

int main(int argc, char **argv) {
    const char *manifest = NULL;
    const char *outpath = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--manifest") == 0 && i + 1 < argc) manifest = argv[++i];
        else if (strcmp(argv[i], "--out") == 0 && i + 1 < argc) outpath = argv[++i];
    }
    if (!manifest || !outpath) return 2;
    FILE *mf = fopen(manifest, "r");
    if (!mf) return 1;
    char line[512];
    FILE *out = fopen(outpath, "w");
    if (!out) { fclose(mf); return 1; }
    fprintf(out, "{\n  \"version\": 1,\n  \"scenarios\": {\n");
    int first = 1;
    while (fgets(line, sizeof line, mf)) {
        char sid[64], cfg[256], trace[256];
        if (sscanf(line, " %63s %255s %255s", sid, cfg, trace) != 3) continue;
        KlbWeave w;
        KlbLatch l;
        char missed[32];
        char chain[3][32];
        int ceilings[8];
        int n_ceil = 0;
        if (stage_a(trace, &w, &l, missed) != 0) continue;
        if (stage_b(cfg, &l, missed, chain, ceilings, &n_ceil) != 0) continue;
        char *gates[8];
        int n_gate = 0;
        FILE *cf = fopen(cfg, "r");
        char cl[256], section[64] = "";
        while (cf && fgets(cl, sizeof cl, cf)) {
            if (cl[0] == '[') {
                char *end = strchr(cl, ']');
                if (!end) continue;
                *end = '\0';
                strncpy(section, cl + 1, 63);
        } else if (strcmp(section, "gates") == 0) {
            char key[64], val[64];
            if (sscanf(cl, " %63[^= ] = %63s", key, val) != 2) continue;
            char *dot = strchr(key, '.');
            if (!dot) continue;
            *dot = '\0';
            if (strcmp(dot + 1, "present") == 0) {
                static char gatebuf[8][32];
                strncpy(gatebuf[n_gate], key, 31);
                gates[n_gate] = gatebuf[n_gate];
                n_gate++;
            }
        }
        }
        if (cf) fclose(cf);
        if (!first) fprintf(out, ",\n");
        first = 0;
        write_json(out, sid, missed, chain, ceilings, n_ceil, (const char **)gates, n_gate);
    }
    fprintf(out, "\n  }\n}\n");
    fclose(out);
    fclose(mf);
    return 0;
}
