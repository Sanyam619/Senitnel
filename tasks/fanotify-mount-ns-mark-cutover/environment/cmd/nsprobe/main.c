#include "../../include/lab.h"
#include "../../lib/state_io.h"
#include <stdio.h>
#include <string.h>

int main(void) {
    char mnt[64];
    if (read_text(MNT_ID, mnt, sizeof(mnt)) != 0) snprintf(mnt, sizeof(mnt), "?");
    printf("identity=%s\n", mnt);

    char gen[64];
    if (read_text(POLICY_GEN, gen, sizeof(gen)) != 0) snprintf(gen, sizeof(gen), "?");
    printf("policy_gen=%s\n", gen);

    char unit[4096];
    if (read_text(UNIT_LIVE, unit, sizeof(unit)) == 0) {
        printf("private=%s\n", strstr(unit, "PrivateMounts=yes") ? "yes" : "no");
    }

    printf("\n");
    for (int i = 0; i < NUM_PATHS; i++) {
        const char *name = ALL_PATHS[i];
        char ht[512], bt[512], hm[512], bm[512];
        char hk[64], bk[64];
        snprintf(ht, sizeof(ht), "%s/%s", HOST_TREE, name);
        snprintf(bt, sizeof(bt), "%s/%s", BROKER_TREE, name);
        snprintf(hm, sizeof(hm), "%s/%s", HOST_MARKS, name);
        snprintf(bm, sizeof(bm), "%s/%s", BROKER_MARKS, name);
        hk[0] = 0;
        bk[0] = 0;
        if (file_exists(hm)) read_text(hm, hk, sizeof(hk));
        if (file_exists(bm)) read_text(bm, bk, sizeof(bk));
        printf("%-14s tree_host=%s tree_broker=%s mark_host=%s mark_broker=%s\n",
               name,
               file_exists(ht) ? "yes" : "-",
               file_exists(bt) ? "yes" : "-",
               file_exists(hm) ? hk : "-",
               file_exists(bm) ? bk : "-");
    }

    printf("\n");
    char table[4096], ok[32], race[64];
    if (read_text(INHERIT_TABLE, table, sizeof(table)) == 0)
        printf("inherit_table=%s\n", table[0] ? table : "(empty)");
    if (read_text(INHERIT_OK, ok, sizeof(ok)) == 0)
        printf("inherit_ok=%s\n", ok);
    if (read_text(RACE_FLAG, race, sizeof(race)) == 0)
        printf("race=%s\n", race);
    return 0;
}
