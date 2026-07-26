#include "io.h"
#include "solver_config.h"
#include <stdio.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <string.h>

static int ensure_dir_json(const char *path) {
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

int json_emit_report(const char *out_path, const scenario_result_t *results,
                     int count, int all_within_budget) {
    /* Ensure the parent directory exists. */
    char dir[512];
    snprintf(dir, sizeof(dir), "%s", out_path);
    char *slash = strrchr(dir, '/');
    if (slash) {
        *slash = '\0';
        ensure_dir_json(dir);
    }

    FILE *fp = fopen(out_path, "w");
    if (!fp) return -1;
    fprintf(fp, "{\n");
    fprintf(fp, "  \"solver_tag\": \"%s\",\n", SOLVER_TAG);
    fprintf(fp, "  \"all_within_budget\": %s,\n",
            all_within_budget ? "true" : "false");
    fprintf(fp, "  \"scenarios\": [\n");
    for (int i = 0; i < count; i++) {
        const scenario_result_t *r = &results[i];
        fprintf(fp, "    {\n");
        fprintf(fp, "      \"label\": \"%s\",\n", r->label);
        fprintf(fp, "      \"iterations\": %d,\n", r->iterations);
        fprintf(fp, "      \"residual\": %.17g,\n", r->residual);
        fprintf(fp, "      \"budget\": %d\n", r->budget);
        fprintf(fp, "    }%s\n", (i == count - 1) ? "" : ",");
    }
    fprintf(fp, "  ]\n");
    fprintf(fp, "}\n");
    fclose(fp);
    return 0;
}
