#include "host.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void outcome_label(int outcome_kind, char *out, size_t n) {
    switch (outcome_kind) {
    case 1: snprintf(out, n, "%s", "promoted"); break;
    case 2: snprintf(out, n, "%s", "held"); break;
    case 3: snprintf(out, n, "%s", "refused"); break;
    default: snprintf(out, n, "%s", "held"); break;
    }
}

void category_label(const struct gate_slot *g, int polymorphic, char *out, size_t n) {
    const char *pick = "held_unclassified";
    if (!g) {
        snprintf(out, n, "%s", pick);
        return;
    }
    if (g->outcome_kind == 3) pick = "interpreter_only";
    else if (g->outcome_kind == 2) {
        if (polymorphic) pick = "held_polymorphic";
        else if (g->bypass_kind == 1) pick = "type_bypass_blocked";
        else if (g->bypass_kind == 2) pick = "arity_bypass_blocked";
        else if (g->bypass_kind == 3) pick = "bounds_bypass_blocked";
        else if (g->bypass_kind == 4) pick = "table_bypass_blocked";
        else pick = "held_unclassified";
    } else if (g->outcome_kind == 1) {
        if (g->benign_kind == 1) pick = "benign_type_stable";
        else if (g->benign_kind == 2) pick = "benign_table_stable";
        else if (g->benign_kind == 3) pick = "benign_epoch_bumped";
        else pick = "promoted_unclassified";
    }
    snprintf(out, n, "%s", pick);
}

static int cmp_id(const void *a, const void *b) {
    return strcmp(((const struct case_out *)a)->id, ((const struct case_out *)b)->id);
}

int emit_report(const char *path, const struct case_out *cases, int n, uint32_t epoch) {
    FILE *fp;
    int i;
    struct case_out sorted[MAX_CASES];
    if (!path || !cases || n < 0 || n > MAX_CASES) return -1;
    memcpy(sorted, cases, (size_t)n * sizeof(*cases));
    if (n > 1) qsort(sorted, (size_t)n, sizeof(*sorted), cmp_id);
    fp = fopen(path, "w");
    if (!fp) return -1;
    fprintf(fp, "{\n");
    fprintf(fp, "  \"schema_version\": \"warmup-report-1\",\n");
    fprintf(fp, "  \"registry_epoch\": %u,\n", epoch);
    fprintf(fp, "  \"scenarios\": [\n");
    for (i = 0; i < n; i++) {
        int first = 1;
        fprintf(fp,
            "    {\"id\": \"%s\", \"outcome\": \"%s\", \"host_call_permitted\": %s, \"category\": \"%s\", \"checks_installed\": [",
            sorted[i].id, sorted[i].outcome,
            sorted[i].host_call_permitted ? "true" : "false",
            sorted[i].category);
        if (sorted[i].check_type)   { fprintf(fp, "%s\"type\"", first ? "" : ", "); first = 0; }
        if (sorted[i].check_arity)  { fprintf(fp, "%s\"arity\"", first ? "" : ", "); first = 0; }
        if (sorted[i].check_bounds) { fprintf(fp, "%s\"bounds\"", first ? "" : ", "); first = 0; }
        if (sorted[i].check_table)  { fprintf(fp, "%s\"table\"", first ? "" : ", "); first = 0; }
        fprintf(fp, "]}%s\n", (i + 1 < n) ? "," : "");
    }
    fprintf(fp, "  ]\n}\n");
    fclose(fp);
    return 0;
}
