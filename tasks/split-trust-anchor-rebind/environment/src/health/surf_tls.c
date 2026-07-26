#include "health.h"
#include "vault.h"
#include <stdio.h>

int surf_tls(void) {
    char root[128];
    if (scan_roots(root, sizeof(root)) != 0) {
        printf("TLS FAIL\n");
        return 1;
    }
    printf("TLS OK\n");
    return 0;
}
