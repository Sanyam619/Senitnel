#define _DEFAULT_SOURCE
#include "seat_slot_b.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int seat_slot_b(const char *a, const char *b, const char *c) {
    (void)c;
    const char *src = (a && a[0]) ? a : HOST_DEV;
    const char *dst = (b && b[0]) ? b : BROKER_DEV;
    ensure_dir(dst);
    (void)src;
    write_text(MNT_ID, "host");
    return 0;
}
