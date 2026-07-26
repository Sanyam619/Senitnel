#include "pinset.h"
#include <stdio.h>
#include <string.h>

static int read_lin(const char *path, char *out, size_t n) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return -1;
    }
    char line[MAX_LINE];
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "lineage=", 8) == 0) {
            snprintf(out, n, "%s", line + 8);
            char *nl = strchr(out, '\n');
            if (nl) {
                *nl = '\0';
            }
            fclose(fp);
            return 0;
        }
    }
    fclose(fp);
    return -1;
}

int load_pin_lines(char *active, char *restore, size_t n) {
    if (read_lin("/app/data/pins/active.set", active, n) != 0) {
        return -1;
    }
    if (read_lin("/app/data/restore/pins.hot", restore, n) != 0) {
        return -1;
    }
    return 0;
}
