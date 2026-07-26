/*
 * reconcile.c — build target for bin/nfsr-reconcile.
 *
 * Reads an episode directory (argv[1]) and emits the aggregate JSON
 * described in docs/reconcile_contract.md on stdout. The default body
 * below emits an empty document; replace it.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "nfsr.h"
#include "journal.h"
#include "state.h"
#include "fh_util.h"

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: nfsr-reconcile <episodes-dir>\n");
        return 2;
    }
    (void)argv;
    printf("{\n");
    printf("  \"episodes\": {}\n");
    printf("}\n");
    return 0;
}
