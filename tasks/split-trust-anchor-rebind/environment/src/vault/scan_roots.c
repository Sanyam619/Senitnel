#include "vault.h"
#include <stdio.h>
#include <string.h>

int scan_roots(char *out, size_t n) {
    FILE *fp = fopen("/app/data/trust/live.bundle", "r");
    if (!fp || !out || n == 0) {
        if (fp) {
            fclose(fp);
        }
        return -1;
    }
    char line[MAX_LINE];
    out[0] = '\0';
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "root=", 5) == 0) {
            snprintf(out, n, "%s", line + 5);
            char *nl = strchr(out, '\n');
            if (nl) {
                *nl = '\0';
            }
            break;
        }
    }
    fclose(fp);
    return 0;
}
