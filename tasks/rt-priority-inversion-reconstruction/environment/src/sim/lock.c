#include <string.h>

int klb_gate_idx(const char gates[][32], int n, const char *id) {
    for (int i = 0; i < n; i++) if (strcmp(gates[i], id) == 0) return i;
    return -1;
}
