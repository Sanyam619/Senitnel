#!/usr/bin/env bash
set -euo pipefail

for tool in topsurf nsprobe ringapply gatecycle racepulse ledgerout unseat remark; do
  if [ ! -x "/opt/fev/bin/$tool" ]; then
    echo "missing helper: $tool" >&2
    exit 1
  fi
done

rm -f /output/mark-cutover.json

cat > /app/ring/apply_ring_a.c <<'EOF'
#include "apply_ring_a.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int apply_ring_a(const char *names_csv, const char *kind) {
    if (!names_csv || !names_csv[0]) return -1;
    const char *mk = (kind && kind[0]) ? kind : "filesystem";

    char buf[512];
    snprintf(buf, sizeof(buf), "%s", names_csv);
    char *save = NULL;
    for (char *tok = strtok_r(buf, ",", &save); tok; tok = strtok_r(NULL, ",", &save)) {
        char bt[512], ht[512], bm[512], hm[512];
        snprintf(bt, sizeof(bt), "%s/%s", BROKER_TREE, tok);
        snprintf(ht, sizeof(ht), "%s/%s", HOST_TREE, tok);
        snprintf(bm, sizeof(bm), "%s/%s", BROKER_MARKS, tok);
        snprintf(hm, sizeof(hm), "%s/%s", HOST_MARKS, tok);

        if (file_exists(bt)) {
            fprintf(stderr, "seat: %s already in broker tree\n", tok);
            return -1;
        }
        if (!file_exists(ht)) {
            fprintf(stderr, "seat: %s not in host tree\n", tok);
            return -1;
        }

        char body[256];
        if (read_text(ht, body, sizeof(body)) != 0) return -1;

        ensure_dir(BROKER_TREE);
        ensure_dir(BROKER_MARKS);
        if (write_text(bt, body) != 0) return -1;
        if (write_text(bm, mk) != 0) return -1;
        unlink(ht);
        if (file_exists(hm)) unlink(hm);
    }

    ensure_dir("/data/lab/identity");
    write_text(MNT_ID, "broker");
    return 0;
}
EOF

cat > /app/gate/cycle_gate_b.c <<'EOF'
#include "cycle_gate_b.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>
#include <string.h>

int cycle_gate_b(const char *a, const char *b, const char *names_csv) {
    (void)a;
    (void)b;
    if (!names_csv || !names_csv[0]) return -1;

    char mnt[64];
    if (read_text(MNT_ID, mnt, sizeof(mnt)) != 0) return -1;
    if (strcmp(mnt, "broker") != 0) {
        fprintf(stderr, "gatecycle: identity not broker\n");
        return -1;
    }

    char unit[4096];
    if (read_text(UNIT_LIVE, unit, sizeof(unit)) != 0) return -1;
    if (strstr(unit, "PrivateMounts=yes") != NULL) {
        fprintf(stderr, "gatecycle: PrivateMounts still yes\n");
        return -1;
    }

    ensure_dir("/data/lab/inherit");
    char table[2048];
    size_t o = 0;
    table[0] = 0;

    char buf[512];
    snprintf(buf, sizeof(buf), "%s", names_csv);
    char *save = NULL;
    for (char *tok = strtok_r(buf, ",", &save); tok; tok = strtok_r(NULL, ",", &save)) {
        char bm[512], kind[64];
        snprintf(bm, sizeof(bm), "%s/%s", BROKER_MARKS, tok);
        if (!file_exists(bm)) {
            fprintf(stderr, "gatecycle: %s has no broker mark\n", tok);
            return -1;
        }
        if (read_text(bm, kind, sizeof(kind)) != 0) return -1;
        if (strcmp(kind, "filesystem") != 0) {
            fprintf(stderr, "gatecycle: %s mark is %s, need filesystem\n", tok, kind);
            return -1;
        }
        char ht[512];
        snprintf(ht, sizeof(ht), "%s/%s", HOST_TREE, tok);
        if (file_exists(ht)) {
            fprintf(stderr, "gatecycle: %s still has host tree entry\n", tok);
            return -1;
        }
        int n = snprintf(table + o, sizeof(table) - o, "%s%s:remount-ok",
                         o ? "\n" : "", tok);
        if (n < 0 || (size_t)n >= sizeof(table) - o) return -1;
        o += (size_t)n;
    }

    if (write_text(INHERIT_TABLE, table) != 0) return -1;
    if (write_text(INHERIT_OK, "1") != 0) return -1;
    return 0;
}
EOF

cat > /app/roll/emit_roll_c.c <<'EOF'
#include "emit_roll_c.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <dirent.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static int fold_one(const char *path) {
    char buf[8192];
    if (read_text(path, buf, sizeof(buf)) != 0) return -1;
    if (strstr(buf, "PrivateMounts=yes") == NULL) return 0;
    char result[8192];
    const char *p = buf;
    size_t o = 0;
    while (*p && o + 1 < sizeof(result)) {
        if (strncmp(p, "PrivateMounts=yes", 17) == 0) {
            const char *rep = "PrivateMounts=no";
            size_t n = strlen(rep);
            memcpy(result + o, rep, n);
            o += n;
            p += 17;
            continue;
        }
        result[o++] = *p++;
    }
    result[o] = 0;
    return write_text(path, result);
}

static int fold_tree(const char *dir) {
    DIR *d = opendir(dir);
    if (!d) return -1;
    struct dirent *ent;
    int rc = 0;
    while ((ent = readdir(d)) != NULL) {
        if (ent->d_name[0] == '.') continue;
        char p[512];
        snprintf(p, sizeof(p), "%s/%s", dir, ent->d_name);
        struct stat st;
        if (stat(p, &st) != 0) continue;
        if (S_ISDIR(st.st_mode)) {
            if (fold_tree(p) != 0) rc = -1;
        } else if (S_ISREG(st.st_mode)) {
            if (fold_one(p) != 0) rc = -1;
        }
    }
    closedir(d);
    return rc;
}

int emit_roll_c(const char *action, const char *out_path) {
    if (!action) return -1;

    if (strcmp(action, "fold") == 0) {
        return fold_tree("/data/lab/units");
    }

    if (strcmp(action, "emit") == 0) {
        const char *dest = (out_path && out_path[0]) ? out_path : OUT_DEFAULT;
        char race[64];
        if (read_text(RACE_FLAG, race, sizeof(race)) != 0)
            snprintf(race, sizeof(race), "dirty");
        int stable = (strcmp(race, "clean") == 0);

        char ok_buf[32];
        if (read_text(INHERIT_OK, ok_buf, sizeof(ok_buf)) != 0)
            snprintf(ok_buf, sizeof(ok_buf), "0");
        int inherit_ok = (strcmp(ok_buf, "1") == 0);

        char table[4096];
        table[0] = 0;
        read_text(INHERIT_TABLE, table, sizeof(table));

        char body[8192];
        size_t o = 0;
        o += (size_t)snprintf(body + o, sizeof(body) - o,
            "{\n  \"version\": 1,\n  \"watches\": [\n");

        for (int i = 0; i < NUM_PATHS; i++) {
            const char *name = ALL_PATHS[i];
            char bm[512], hm[512], bt[512], ht[512];
            snprintf(bm, sizeof(bm), "%s/%s", BROKER_MARKS, name);
            snprintf(hm, sizeof(hm), "%s/%s", HOST_MARKS, name);
            snprintf(bt, sizeof(bt), "%s/%s", BROKER_TREE, name);
            snprintf(ht, sizeof(ht), "%s/%s", HOST_TREE, name);

            const char *ns = "unknown";
            char kind[64];
            kind[0] = 0;

            if (file_exists(bt) && file_exists(bm)) {
                ns = "broker";
                read_text(bm, kind, sizeof(kind));
            } else if (file_exists(ht) && file_exists(hm)) {
                ns = "host";
                read_text(hm, kind, sizeof(kind));
            } else if (file_exists(bm)) {
                ns = "broker";
                read_text(bm, kind, sizeof(kind));
            } else if (file_exists(hm)) {
                ns = "host";
                read_text(hm, kind, sizeof(kind));
            }

            char token[128];
            snprintf(token, sizeof(token), "%s:remount-ok", name);
            int path_inherited = inherit_ok && (strstr(table, token) != NULL);

            char jp[512];
            snprintf(jp, sizeof(jp), "%s/%s", HOST_JITTER, name);
            int path_stable = stable && !file_exists(jp);

            if (i > 0)
                o += (size_t)snprintf(body + o, sizeof(body) - o, ",\n");
            o += (size_t)snprintf(body + o, sizeof(body) - o,
                "    {\"path\": \"%s\", \"mark_ns\": \"%s\", \"mark_kind\": \"%s\", "
                "\"inherited_ok\": %s, \"race_stable\": %s}",
                name, ns, kind,
                path_inherited ? "true" : "false",
                path_stable ? "true" : "false");
        }

        o += (size_t)snprintf(body + o, sizeof(body) - o, "\n  ]\n}\n");
        ensure_dir("/output");
        return write_text(dest, body);
    }

    return -1;
}
EOF

echo "== rebuild helpers =="
if ! (cd /app && make clean && make); then
  echo "rebuild failed" >&2
  exit 1
fi
cp -f /app/bin/* /opt/fev/bin/
chmod +x /opt/fev/bin/*

echo "== advance policy generation =="
echo -n 'g3' > /data/lab/identity/policy_gen

echo "== fold private mounts (unit + drop-ins) =="
/opt/fev/bin/ledgerout --fold
if grep -Rq 'PrivateMounts=yes' /data/lab/units; then
  echo "PrivateMounts still yes under units" >&2
  exit 1
fi

echo "== fix path-beta mark kind =="
/opt/fev/bin/remark --path path-beta --kind filesystem

echo "== clean path-gamma dual presence =="
rm -f /data/lab/trees/host/path-gamma

echo "== unseat path-epsilon =="
/opt/fev/bin/unseat --names path-epsilon

echo "== seat path-delta =="
/opt/fev/bin/ringapply --names path-delta --kind filesystem

echo "== inherit cycle (g3 roster order) =="
/opt/fev/bin/gatecycle --names "path-delta,path-alpha,path-gamma,path-beta"

echo "== race barrier =="
if ! /opt/fev/bin/racepulse; then
  echo "race dirty" >&2
  exit 1
fi

echo "== emit ledger =="
/opt/fev/bin/ledgerout --emit --out /output/mark-cutover.json
[ -f /output/mark-cutover.json ] || { echo "missing report"; exit 1; }

python3 - /output/mark-cutover.json <<'PY'
import json, sys
from pathlib import Path
assert Path("/data/lab/identity/policy_gen").read_text().strip() == "g3"
payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["version"] == 1
rows = {r["path"]: r for r in payload["watches"]}
for name in ("path-alpha", "path-beta", "path-gamma", "path-delta"):
    r = rows[name]
    assert r["mark_ns"] == "broker", (name, r)
    assert r["mark_kind"] == "filesystem", (name, r)
    assert r["inherited_ok"] is True, (name, r)
    assert r["race_stable"] is True, (name, r)
for name in ("path-epsilon", "path-zeta"):
    r = rows[name]
    assert r["mark_ns"] == "host", (name, r)
    assert r["mark_kind"] == "inode", (name, r)
    assert r["inherited_ok"] is False, (name, r)
    assert r["race_stable"] is True, (name, r)
print("oracle ledger ok")
PY

echo "cutover complete"
