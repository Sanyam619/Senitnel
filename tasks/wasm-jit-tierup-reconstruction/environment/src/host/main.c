#include "host.h"
#include "tier_a.h"
#include "tier_b.h"
#include "tier_c.h"
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int load_one(const char *id, struct scenario_in *sc,
                    struct profile_view *pv, struct rebind_view *rv,
                    struct floor_view *fv) {
    char path[MAX_PATH];
    snprintf(path, sizeof(path), "/app/data/scenarios/%s.case", id);
    if (load_scenario(path, sc) != 0) return -1;
    snprintf(path, sizeof(path), "/app/data/authority/profile/%s.prof", id);
    if (load_profile(path, pv) != 0) return -1;
    snprintf(path, sizeof(path), "/app/data/authority/rebind/%s.rbnd", id);
    if (load_rebind(path, rv) != 0) return -1;
    snprintf(path, sizeof(path), "/app/data/authority/floor/%s.flr", id);
    if (load_floor(path, fv) != 0) return -1;
    return 0;
}

int main(int argc, char **argv) {
    struct scenario_in sc;
    struct profile_view pv;
    struct rebind_view rv;
    struct floor_view fv;
    struct profile_slot ps;
    struct rebind_slot rs;
    struct gate_slot gs;
    struct case_out outs[MAX_CASES];
    char ids[MAX_CASES][MAX_ID];
    uint32_t manifest_epoch = 0;
    uint32_t decision_epoch;
    const char *out_path;
    DIR *d;
    struct dirent *ent;
    int n = 0, i;

    if (argc < 2) {
        fprintf(stderr, "usage: warmup <output-path>\n");
        return 2;
    }
    out_path = argv[1];

    if (read_registry_epoch("/app/data/manifest/registry.sig", &manifest_epoch) != 0) {
        fprintf(stderr, "registry read failed\n");
        return 1;
    }

    d = opendir("/app/data/scenarios");
    if (!d) return 1;
    while ((ent = readdir(d)) != NULL && n < MAX_CASES) {
        size_t len = strlen(ent->d_name);
        if (len < 6 || strcmp(ent->d_name + len - 5, ".case") != 0) continue;
        snprintf(ids[n], MAX_ID, "%.*s", (int)(len - 5), ent->d_name);
        n++;
    }
    closedir(d);

    for (i = 0; i < n; i++) {
        if (load_one(ids[i], &sc, &pv, &rv, &fv) != 0) {
            fprintf(stderr, "load failed for %s\n", ids[i]);
            return 1;
        }
        decision_epoch = manifest_epoch;
        if (fold_profile(&pv, &ps) != 0) return 1;
        if (fold_rebind(&rv, &rs) != 0) return 1;
        if (fold_gate(&sc, &ps, &rs, &fv, decision_epoch, &gs) != 0) return 1;

        memset(&outs[i], 0, sizeof(outs[i]));
        snprintf(outs[i].id, sizeof(outs[i].id), "%s", sc.id);
        outcome_label(gs.outcome_kind, outs[i].outcome, sizeof(outs[i].outcome));
        outs[i].host_call_permitted = gs.host_call_permitted ? 1 : 0;
        outs[i].check_type = gs.check_type;
        outs[i].check_arity = gs.check_arity;
        outs[i].check_bounds = gs.check_bounds;
        outs[i].check_table = gs.check_table;
        category_label(&gs, ps.polymorphic, outs[i].category, sizeof(outs[i].category));
    }

    if (emit_report(out_path, outs, n, manifest_epoch) != 0) {
        fprintf(stderr, "emit failed\n");
        return 1;
    }
    return 0;
}
