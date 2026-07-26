#include "klb_sim.h"
#include "klb_fmt.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int parse_ceilings(const char *blob, const char *sid, char gates[][32], int ceilings[], int cap) {
    char needle[128];
    snprintf(needle, sizeof needle, "\"%s\"", sid);
    const char *pos = strstr(blob, needle);
    if (!pos) return -1;
    const char *cpos = strstr(pos, "\"ceilings\"");
    if (!cpos) return -1;
    const char *start = strchr(cpos, '{');
    const char *end = strchr(start, '}');
    if (!start || !end) return -1;
    int n = 0;
    const char *p = start + 1;
    while (p < end && n < cap) {
        p = strchr(p, '"');
        if (!p || p >= end) break;
        p++;
        char key[32];
        int ki = 0;
        while (*p && *p != '"' && ki + 1 < (int)sizeof key) key[ki++] = *p++;
        key[ki] = '\0';
        p = strchr(p, ':');
        if (!p || p >= end) break;
        p++;
        while (*p == ' ') p++;
        ceilings[n] = atoi(p);
        strncpy(gates[n], key, 31);
        n++;
        p++;
    }
    return n;
}

int main(int argc, char **argv) {
    const char *cfg = NULL;
    const char *trace = NULL;
    const char *analysis = NULL;
    const char *sid = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--cfg") == 0 && i + 1 < argc) cfg = argv[++i];
        else if (strcmp(argv[i], "--trace") == 0 && i + 1 < argc) trace = argv[++i];
        else if (strcmp(argv[i], "--analysis") == 0 && i + 1 < argc) analysis = argv[++i];
        else if (strcmp(argv[i], "--scenario") == 0 && i + 1 < argc) sid = argv[++i];
    }
    if (!cfg || !trace || !analysis || !sid) return 2;
    FILE *af = fopen(analysis, "r");
    if (!af) return 1;
    char blob[65536];
    size_t n = fread(blob, 1, sizeof blob - 1, af);
    blob[n] = '\0';
    fclose(af);
    char gates[8][32];
    int ceilings[8];
    int n_ceil = parse_ceilings(blob, sid, gates, ceilings, 8);
    if (n_ceil < 1) return 1;
    KlbReplayResult res;
    if (klb_replay_scenario(cfg, trace, gates, ceilings, n_ceil, &res) != 0) return 1;
    printf("{\"misses\": %d}\n", res.misses);
    return 0;
}
