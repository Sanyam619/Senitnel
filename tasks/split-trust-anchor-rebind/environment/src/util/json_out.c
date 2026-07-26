#include "common.h"
#include <stdio.h>
#include <string.h>

int json_emit_ledger(const char *path, const struct case_out *cases, int n, uint32_t reload_epoch) {
    FILE *fp = fopen(path, "w");
    int i;
    if (!fp) {
        return -1;
    }
    fprintf(fp, "{\n");
    fprintf(fp, "  \"schema_version\": \"edge-admit-1\",\n");
    fprintf(fp, "  \"reload_epoch\": %u,\n", reload_epoch);
    fprintf(fp, "  \"cases\": [\n");
    for (i = 0; i < n; i++) {
        fprintf(fp,
                "    {\"id\": \"%s\", \"decision\": \"%s\", \"reason_code\": \"%s\"}%s\n",
                cases[i].id,
                cases[i].decision,
                cases[i].reason_code,
                (i + 1 < n) ? "," : "");
    }
    fprintf(fp, "  ]\n");
    fprintf(fp, "}\n");
    fclose(fp);
    return 0;
}
