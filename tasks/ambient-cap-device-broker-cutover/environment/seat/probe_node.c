#include "probe_node.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <dirent.h>
#include <stdio.h>
#include <string.h>

/* Host-tree listing only — never moves entries. */
int probe_node(const char *a) {
    const char *dir = (a && a[0]) ? a : HOST_DEV;
    DIR *d = opendir(dir);
    if (!d) {
        printf("probe: empty\n");
        return 0;
    }
    struct dirent *e;
    while ((e = readdir(d)) != NULL) {
        if (e->d_name[0] == '.') continue;
        printf("%s\n", e->d_name);
    }
    closedir(d);
    return 0;
}
