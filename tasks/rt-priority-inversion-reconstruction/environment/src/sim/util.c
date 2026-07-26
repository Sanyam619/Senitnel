#include <ctype.h>
#include <stdio.h>
#include <string.h>

int klb_skip_comment(const char *line) {
    while (*line && isspace((unsigned char)*line)) line++;
    return *line == '#' || *line == '\0';
}

int klb_read_field(const char *line, int idx, char *out, int outlen) {
    const char *p = line;
    for (int i = 0; i < idx; i++) {
        while (*p && !isspace((unsigned char)*p)) p++;
        while (*p && isspace((unsigned char)*p)) p++;
        if (!*p) return -1;
    }
    int n = 0;
    while (*p && !isspace((unsigned char)*p) && n + 1 < outlen) out[n++] = *p++;
    out[n] = '\0';
    return n > 0 ? 0 : -1;
}
