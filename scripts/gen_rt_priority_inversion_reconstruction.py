#!/usr/bin/env python3
"""Generate tasks/rt-priority-inversion-reconstruction (authoring tool, not shipped)."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "rt-priority-inversion-reconstruction"
ENV = ROOT / "environment"
SPECS = Path(__file__).resolve().parents[1] / "specs"
OPT = "/opt/kernlab"

SCENARIOS = {
    "case_nova": {
        "missed": "t_charlie",
        "chain": ["t_charlie", "t_alpha", "t_bravo"],
        "ceilings": {"lk_one": 10},
        "tasks": {
            "t_charlie": {"prio": 10, "period_us": 100000, "locks": ["lk_one"]},
            "t_bravo": {"prio": 5, "period_us": 0, "locks": []},
            "t_alpha": {"prio": 1, "period_us": 0, "locks": ["lk_one"]},
        },
        "locks": ["lk_one"],
    },
    "case_orbit": {
        "missed": "t_helix",
        "chain": ["t_helix", "t_spoke", "t_rim"],
        "ceilings": {"lk_a": 8, "lk_b": 8},
        "tasks": {
            "t_helix": {"prio": 8, "period_us": 80000, "locks": ["lk_a", "lk_b"]},
            "t_spoke": {"prio": 3, "period_us": 0, "locks": ["lk_a"]},
            "t_rim": {"prio": 6, "period_us": 0, "locks": []},
        },
        "locks": ["lk_a", "lk_b"],
    },
    "case_pulse": {
        "missed": "t_beacon",
        "chain": ["t_beacon", "t_drift", "t_glide"],
        "ceilings": {"lk_c": 9},
        "tasks": {
            "t_beacon": {"prio": 9, "period_us": 50000, "locks": ["lk_c"]},
            "t_drift": {"prio": 2, "period_us": 0, "locks": ["lk_c"]},
            "t_glide": {"prio": 4, "period_us": 0, "locks": []},
        },
        "locks": ["lk_c"],
    },
    "case_delta": {
        "missed": "t_siren",
        "chain": ["t_siren", "t_moor", "t_tide"],
        "ceilings": {"lk_d": 10},
        "tasks": {
            "t_siren": {"prio": 10, "period_us": 120000, "locks": ["lk_d"]},
            "t_moor": {"prio": 1, "period_us": 0, "locks": ["lk_d"]},
            "t_tide": {"prio": 7, "period_us": 0, "locks": []},
        },
        "locks": ["lk_d"],
    },
    "case_eclipse": {
        "missed": "t_axis",
        "chain": ["t_axis", "t_pivot", "t_orbit"],
        "ceilings": {"lk_p": 7},
        "tasks": {
            "t_axis": {"prio": 7, "period_us": 70000, "locks": ["lk_p"]},
            "t_pivot": {"prio": 2, "period_us": 0, "locks": ["lk_p"]},
            "t_orbit": {"prio": 5, "period_us": 0, "locks": []},
        },
        "locks": ["lk_p"],
    },
    "case_zenith": {
        "missed": "t_vega",
        "chain": ["t_vega", "t_anchor", "t_dome"],
        "ceilings": {"lk_m": 11, "lk_s": 11},
        "tasks": {
            "t_vega": {"prio": 11, "period_us": 110000, "locks": ["lk_m", "lk_s"]},
            "t_anchor": {"prio": 1, "period_us": 0, "locks": ["lk_m"]},
            "t_dome": {"prio": 8, "period_us": 0, "locks": []},
        },
        "locks": ["lk_m", "lk_s"],
    },
}

TRACES = {
    "case_nova": """\
# klb evt v1
JOB 0 t_charlie START
TSW 1000 t_charlie t_alpha
LCK 1100 t_alpha lk_one ACQ
JOB 1200 t_alpha START
TSW 15000 t_alpha t_bravo
JOB 16000 t_bravo START
WUP 20000 t_bravo t_charlie
LCK 25000 t_charlie lk_one WAIT
TMR 100000 t_charlie job0 EXP 100000
TSW 105000 t_bravo t_charlie
LCK 106000 t_charlie lk_one ACQ
JOB 106100 t_charlie START
JOB 120000 t_charlie END
LCK 120100 t_charlie lk_one REL
TSW 120200 t_charlie t_alpha
LCK 120300 t_alpha lk_one REL
""",
    "case_orbit": """\
# klb evt v1
JOB 0 t_helix START
TSW 500 t_helix t_spoke
LCK 800 t_spoke lk_a ACQ
JOB 900 t_spoke START
TSW 12000 t_spoke t_rim
JOB 13000 t_rim START
WUP 15000 t_rim t_helix
LCK 18000 t_helix lk_a WAIT
TMR 80000 t_helix job0 EXP 80000
TSW 82000 t_rim t_helix
LCK 82500 t_helix lk_a ACQ
LCK 83000 t_helix lk_b ACQ
JOB 83500 t_helix START
JOB 85000 t_helix END
LCK 85100 t_helix lk_b REL
LCK 85200 t_helix lk_a REL
LCK 85300 t_spoke lk_a REL
""",
    "case_pulse": """\
# klb evt v1
JOB 0 t_beacon START
TSW 200 t_beacon t_drift
LCK 400 t_drift lk_c ACQ
JOB 500 t_drift START
WUP 800 t_drift t_glide
TSW 2000 t_drift t_glide
JOB 2100 t_glide START
WUP 5000 t_glide t_beacon
LCK 7000 t_beacon lk_c WAIT
TMR 50000 t_beacon job0 EXP 50000
TSW 52000 t_glide t_beacon
LCK 52500 t_beacon lk_c ACQ
JOB 53000 t_beacon START
JOB 56000 t_beacon END
LCK 56100 t_beacon lk_c REL
LCK 56200 t_drift lk_c REL
""",
    "case_delta": """\
# klb evt v1
JOB 0 t_siren START
TSW 300 t_siren t_moor
LCK 600 t_moor lk_d ACQ
JOB 700 t_moor START
TSW 10000 t_moor t_tide
JOB 11000 t_tide START
WUP 14000 t_tide t_siren
LCK 16000 t_siren lk_d WAIT
TMR 120000 t_siren job0 EXP 120000
TSW 121000 t_tide t_siren
LCK 121500 t_siren lk_d ACQ
JOB 121600 t_siren START
JOB 135000 t_siren END
LCK 135100 t_siren lk_d REL
""",
    "case_eclipse": """\
# klb evt v1
JOB 0 t_axis START
TSW 800 t_axis t_pivot
LCK 900 t_pivot lk_p ACQ
LCK 85000 t_pivot lk_p REL
JOB 1000 t_pivot START
TSW 11000 t_pivot t_orbit
JOB 12000 t_orbit START
WUP 14000 t_orbit t_axis
LCK 17000 t_axis lk_p WAIT
TMR 70000 t_axis job0 EXP 70000
TSW 72000 t_orbit t_axis
LCK 72500 t_axis lk_p ACQ
JOB 73000 t_axis START
JOB 80000 t_axis END
LCK 80100 t_axis lk_p REL
""",
    "case_zenith": """\
# klb evt v1
JOB 0 t_vega START
TSW 600 t_vega t_anchor
LCK 900 t_anchor lk_m ACQ
LCK 950 t_anchor lk_s ACQ
JOB 1100 t_anchor START
TSW 14000 t_anchor t_dome
JOB 15000 t_dome START
WUP 18000 t_dome t_vega
LCK 22000 t_vega lk_m WAIT
TMR 110000 t_vega job0 EXP 110000
TSW 112000 t_dome t_vega
LCK 112500 t_vega lk_m ACQ
LCK 113000 t_vega lk_s ACQ
JOB 113500 t_vega START
JOB 118000 t_vega END
LCK 118100 t_vega lk_s REL
LCK 118200 t_vega lk_m REL
LCK 118300 t_anchor lk_s REL
LCK 118400 t_anchor lk_m REL
""",
}


def w(rel: str, content: str) -> None:
    p = ROOT / rel if not rel.startswith("environment/") else ENV / rel.removeprefix("environment/")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def main() -> None:
  write_spec()
  write_headers()
  write_sim_sources()
  write_probe_sources()
  write_packaging()
  write_configs()
  write_traces()
  write_docs()
  write_makefile()
  write_dockerfile()
  write_dockerignore()
  write_task_meta()
  write_instruction()
  write_tests()
  write_solution()
  cleanup_stale_paths()
  print(f"generated {ROOT}")


def cleanup_stale_paths() -> None:
  stale = [
    "environment/src/a7",
    "environment/src/m3",
    "environment/src/q9",
    "environment/src/w2",
    "environment/src/probe/scan.c",
    "environment/src/probe/replay_main.c",
  ]
  for rel in stale:
    p = ROOT / rel
    if p.is_dir():
      import shutil
      shutil.rmtree(p)
    elif p.is_file():
      p.unlink()
  import glob
  for obj in glob.glob(str(ENV / "**" / "*.o"), recursive=True):
    Path(obj).unlink(missing_ok=True)
  for name in ("kernprobe", "klreplay"):
    p = ENV / name
    if p.is_file():
      p.unlink()


def write_spec() -> None:
  spec = """\
### Decision
GO — Attempt 1. Original RT trace reconstruction task; distributed C fix path with opaque weave/latch/band/map symbols.

### Metadata
- version: 2
- Task name: rt-priority-inversion-reconstruction
- Title: RT Inversion Rebuild
- Category: scientific-computing
- Languages: ["C"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["c", "real-time", "scheduling", "trace", "simulation", "scientific-computing"]
- Milestones: 0

## Authoring Brief

### Public contract
Agent rebuilds `/opt/kernlab/bin/kernprobe` and runs `/opt/kernlab/bin/kernprobe --manifest /opt/kernlab/config/manifest.json --out /output/analysis.json`. Each manifest scenario id must appear under `scenarios` with `missed_deadline_task`, ordered `chain` of three actor ids, and integer `ceilings` map keyed by gate ids. The bundled replay tool `/opt/kernlab/bin/klreplay` must report zero misses when driven with the emitted ceilings. Event layout and set catalog live under `/opt/kernlab/docs/`.

### Failure topology
Recorded runs show periodic actors missing release windows while a mid-band runnable keeps the CPU. The stock probe names only the immediate gate holder, drops waiters after context changes, and assigns ceilings from the holder band instead of the waiter band. Replay proof fails on every manifest row.

### Environment shape
C tree under `/opt/kernlab` with deterministic replay core, probe CLI, opaque modules under `kern/a7`, `relay/m3`, `span/q9`, `lift/w2`, trace corpus, per-case set configs, manifest.

### Required artifacts
instruction.md, task.toml, output_contract.toml, Dockerfile, .dockerignore, Makefile, 24+ environment files, solve.sh, test.sh, test_outputs.py.

### Test plan
- test_h4_schema_bundle — analysis.json version and per-scenario keys
- test_u2_nova_chain — case_nova chain triple
- test_k7_orbit_chain — case_orbit chain triple
- test_m3_pulse_chain — case_pulse chain triple
- test_p9_delta_chain — case_delta chain triple
- test_q1_nova_replay — klreplay zero misses for nova ceilings
- test_r5_orbit_replay — klreplay zero misses for orbit ceilings
- test_s8_pulse_replay — klreplay zero misses for pulse ceilings
- test_t2_delta_replay — klreplay zero misses for delta ceilings

### Drafting guardrails
Symptoms-only instruction; opaque fix-path symbols; expected chains live in tests only.

### Triviality Ledger
- Direct-holder scan passes one field but fails chain tests because band module ignores preemptor.
- Timestamp-only weave passes sorting but mis-attributes waiters after wakeups.
- Holder-band ceilings pass replay on trivial rows but fail delta and orbit deadline windows.

### Per-gate Pitfall Inventory
- RC3: tests compare chain triples and replay miss counts, not file existence.
- RC6: instruction describes symptoms and output schema, not weave/latch/band/map internals.
- RC7: oracle rewrites four modules with substantive timeline/ownership/chain/ceiling logic.
- CR7: fix-path symbols op_weave, op_latch, op_span, op_lift avoid instruction nouns.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- environment/Dockerfile
- environment/.dockerignore
- environment/Makefile
- environment/include/klb_fmt.h
- environment/include/klb_sim.h
- environment/include/klb_types.h
- environment/src/sim/core.c
- environment/src/sim/queue.c
- environment/src/sim/lock.c
- environment/src/sim/deadline.c
- environment/src/sim/replay.c
- environment/src/sim/util.c
- environment/src/probe/main.c
- environment/src/probe/stage_a.c
- environment/src/probe/stage_b.c
- environment/kern/a7/weave.c
- environment/kern/a7/hash.c
- environment/relay/m3/latch.c
- environment/relay/m3/shadow.c
- environment/span/q9/span.c
- environment/span/q9/ring.c
- environment/lift/w2/lift.c
- environment/config/manifest.json
- environment/config/case_nova.toml
- environment/config/case_orbit.toml
- environment/config/case_pulse.toml
- environment/config/case_delta.toml
- environment/traces/case_nova.evt
- environment/traces/case_orbit.evt
- environment/traces/case_pulse.evt
- environment/traces/case_delta.evt
- environment/docs/event_layout.txt
- environment/docs/set_catalog.txt
- environment/scripts/smoke.sh
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py
- tests/chain_ref.py

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: kern/a7/weave.c
  symbol: op_weave
  kind: function
  signature: int op_weave(const char *path, KlbWeave *out)
  purpose: parse trace file into ordered actor timeline with wait edges
- path: relay/m3/latch.c
  symbol: op_latch
  kind: function
  signature: int op_latch(const KlbWeave *w, KlbLatch *out)
  purpose: derive gate holder and waiter sets at each step
- path: span/q9/span.c
  symbol: op_span
  kind: function
  signature: int op_span(const KlbLatch *l, const char *tgt, char chain[3][32])
  purpose: locate three-actor blocking span including mid-band preemptor
- path: lift/w2/lift.c
  symbol: op_lift
  kind: function
  signature: int op_lift(const char *cfg, const char *tgt, int *ceilings, int cap)
  purpose: compute static band map from set catalog and waiter band

#### flipping_point_contract
locations:
  - id: A
    path: kern/a7/weave.c
    controls_tests: [test_m3_pulse_chain, test_u2_nova_chain]
  - id: B
    path: relay/m3/latch.c
    controls_tests: [test_k7_orbit_chain, test_p9_delta_chain]
  - id: C
    path: span/q9/span.c
    controls_tests: [test_u2_nova_chain, test_k7_orbit_chain, test_m3_pulse_chain, test_p9_delta_chain]
  - id: D
    path: lift/w2/lift.c
    controls_tests: [test_q1_nova_replay, test_r5_orbit_replay, test_s8_pulse_replay, test_t2_delta_replay]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: kern/a7/hash.c
  kind: helper
  rhymes_with: op_weave
  non_fix_purpose: fingerprint rows for manifest validation
- path: relay/m3/shadow.c
  kind: helper
  rhymes_with: op_latch
  non_fix_purpose: shadow table for debug dumps
- path: span/q9/ring.c
  kind: helper
  rhymes_with: op_span
  non_fix_purpose: ring buffer for probe stderr

#### code_forbidden_tokens
code_forbidden_tokens: [periodic, deadline, trace, event, lock, acquire, release, wakeup, timer, scheduler, simulator, replay, priority, inversion, chain, holder, waiter, preemptor, runqueue, timeline, ownership, ceiling, assignment, analysis, scenario, task, reconstruction, missed, preempt, periodic]
"""
  (SPECS / "rt-priority-inversion-reconstruction.md").write_text(spec, encoding="utf-8")


def write_headers() -> None:
  w("environment/include/klb_types.h", """\
  #ifndef KLB_TYPES_H
  #define KLB_TYPES_H

  #include <stdint.h>

  #define KLB_MAX_ACTORS 16
  #define KLB_MAX_GATES 8
  #define KLB_MAX_STEPS 512

  typedef struct {
      char actor[32];
      char gate[32];
      int is_wait;
      int is_rel;
      int64_t ts;
  } KlbGateEvt;

  typedef struct {
      char prev[32];
      char next[32];
      int64_t ts;
  } KlbSwitchEvt;

  typedef struct {
      int n_gate;
      int n_switch;
      KlbGateEvt gate[KLB_MAX_STEPS];
      KlbSwitchEvt sw[KLB_MAX_STEPS];
      char missed[32];
      int64_t miss_ts;
  } KlbWeave;

  typedef struct {
      char holder[KLB_MAX_GATES][32];
      char waiters[KLB_MAX_GATES][KLB_MAX_ACTORS][32];
      int n_waiters[KLB_MAX_GATES];
      char running[32];
      int64_t at_ts;
  } KlbLatch;

  #endif
  """)

  w("environment/include/klb_fmt.h", """\
  #ifndef KLB_FMT_H
  #define KLB_FMT_H

  #include "klb_types.h"

  int klb_parse_trace(const char *path, KlbWeave *out);
  int klb_load_set(const char *path, char actors[][32], int prios[], char gates[][32], int *n_act, int *n_gate);

  #endif
  """)

  w("environment/include/klb_sim.h", """\
  #ifndef KLB_SIM_H
  #define KLB_SIM_H

  #include <stdint.h>

  typedef struct {
      char scenario[64];
      int misses;
  } KlbReplayResult;

  int klb_replay_scenario(const char *cfg, const char *trace, const char ceil_gates[][32], const int *ceilings, int n_ceil, KlbReplayResult *res);

  #endif
  """)


def write_sim_sources() -> None:
  w("environment/src/sim/util.c", """\
  #include <ctype.h>
  #include <stdio.h>
  #include <string.h>

  int klb_skip_comment(const char *line) {
      while (*line && isspace((unsigned char)*line)) line++;
      return *line == '#' || *line == '\\0';
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
      out[n] = '\\0';
      return n > 0 ? 0 : -1;
  }
  """)

  w("environment/src/sim/core.c", """\
  #include "klb_fmt.h"
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>

  static int read_prio_toml(const char *path, const char *actor, int *prio) {
      FILE *f = fopen(path, "r");
      if (!f) return -1;
      char line[256];
      char section[64] = "";
      while (fgets(line, sizeof line, f)) {
          if (line[0] == '[') {
              char *end = strchr(line, ']');
              if (!end) continue;
              *end = '\\0';
              strncpy(section, line + 1, sizeof section - 1);
              continue;
          }
          if (strcmp(section, "actors") != 0) continue;
          char key[64], val[64];
          if (sscanf(line, " %63[^= ] = %63s", key, val) != 2) continue;
          char *dot = strchr(key, '.');
          if (!dot) continue;
          *dot = '\\0';
          if (strcmp(key, actor) == 0 && strcmp(dot + 1, "band") == 0) {
              *prio = atoi(val);
              fclose(f);
              return 0;
          }
      }
      fclose(f);
      return -1;
  }

  int klb_load_set(const char *path, char actors[][32], int prios[], char gates[][32], int *n_act, int *n_gate) {
      FILE *f = fopen(path, "r");
      if (!f) return -1;
      *n_act = 0;
      *n_gate = 0;
      char line[256];
      char section[64] = "";
      while (fgets(line, sizeof line, f)) {
          if (line[0] == '[') {
              char *end = strchr(line, ']');
              if (!end) continue;
              *end = '\\0';
              strncpy(section, line + 1, sizeof section - 1);
              continue;
          }
          char key[64], val[64];
          if (sscanf(line, " %63[^= ] = %63s", key, val) != 2) continue;
          if (strcmp(section, "actors") == 0) {
              char *dot = strchr(key, '.');
              if (!dot) continue;
              *dot = '\\0';
              int idx = -1;
              for (int i = 0; i < *n_act; i++) if (strcmp(actors[i], key) == 0) idx = i;
              if (idx < 0) {
                  idx = (*n_act)++;
                  strncpy(actors[idx], key, 31);
              }
              if (strcmp(dot + 1, "band") == 0) prios[idx] = atoi(val);
          } else if (strcmp(section, "gates") == 0) {
              char key[64], val[64];
              if (sscanf(line, " %63[^= ] = %63s", key, val) != 2) continue;
              char *dot = strchr(key, '.');
              if (!dot) continue;
              *dot = '\\0';
              if (strcmp(dot + 1, "present") == 0) {
                  strncpy(gates[(*n_gate)++], key, 31);
              }
          }
      }
      fclose(f);
      (void)read_prio_toml;
      return 0;
  }

  int klb_parse_trace(const char *path, KlbWeave *out) {
      FILE *f = fopen(path, "r");
      if (!f) return -1;
      memset(out, 0, sizeof *out);
      char line[512];
      while (fgets(line, sizeof line, f)) {
          if (line[0] == '#') continue;
          char tag[16];
          if (sscanf(line, "%15s", tag) != 1) continue;
          if (strcmp(tag, "LCK") == 0) {
              KlbGateEvt *e = &out->gate[out->n_gate++];
              sscanf(line, "%*s %lld %31s %31s", (long long *)&e->ts, e->actor, e->gate);
              char op[16];
              sscanf(line, "%*s %*s %*s %*s %15s", op);
              e->is_wait = (strcmp(op, "WAIT") == 0);
              e->is_rel = (strcmp(op, "REL") == 0);
          } else if (strcmp(tag, "TSW") == 0) {
              KlbSwitchEvt *s = &out->sw[out->n_switch++];
              sscanf(line, "%*s %lld %31s %31s", (long long *)&s->ts, s->prev, s->next);
          } else if (strcmp(tag, "TMR") == 0) {
              char op[16];
              char who[32];
              int64_t ts, dl;
              sscanf(line, "%*s %lld %31s %*s %15s %lld", (long long *)&ts, who, op, (long long *)&dl);
              if (strcmp(op, "EXP") == 0) {
                  strncpy(out->missed, who, 31);
                  out->miss_ts = ts;
              }
          }
      }
      fclose(f);
      return 0;
  }
  """)

  w("environment/src/sim/queue.c", """\
  #include <string.h>

  int klb_pick_runnable(const char *running, const char actors[][32], const int prios[], int n, const int effective[]) {
      int best = -1;
      int bestp = -1;
      for (int i = 0; i < n; i++) {
          int p = effective[i] > 0 ? effective[i] : prios[i];
          if (p > bestp) { bestp = p; best = i; }
      }
      (void)running;
      return best;
  }
  """)

  w("environment/src/sim/lock.c", """\
  #include <string.h>

  int klb_gate_idx(const char gates[][32], int n, const char *id) {
      for (int i = 0; i < n; i++) if (strcmp(gates[i], id) == 0) return i;
      return -1;
  }
  """)

  w("environment/src/sim/deadline.c", """\
  #include <stdint.h>

  int klb_deadline_met(int64_t finish, int64_t deadline) {
      return finish <= deadline ? 1 : 0;
  }
  """)

  w("environment/src/sim/replay.c", """\
  #include "klb_sim.h"
  #include "klb_fmt.h"
  #include <stdio.h>
  #include <string.h>

  int klb_replay_scenario(const char *cfg, const char *trace, const char ceil_gates[][32], const int *ceilings, int n_ceil, KlbReplayResult *res) {
      char actors[16][32];
      char gates[8][32];
      int prios[16];
      int n_act = 0, n_gate = 0;
      if (klb_load_set(cfg, actors, prios, gates, &n_act, &n_gate) != 0) return -1;
      KlbWeave w;
      if (klb_parse_trace(trace, &w) != 0) return -1;
      int wait_band = 0;
      for (int ai = 0; ai < n_act; ai++) {
          if (strcmp(actors[ai], w.missed) == 0) wait_band = prios[ai];
      }
      int misses = 0;
      for (int gi = 0; gi < n_gate; gi++) {
          int ceil = 0;
          for (int ci = 0; ci < n_ceil; ci++) {
              if (strcmp(gates[gi], ceil_gates[ci]) == 0) {
                  ceil = ceilings[ci];
                  break;
              }
          }
          if (ceil < wait_band) misses = 1;
      }
      strncpy(res->scenario, cfg, 63);
      res->misses = misses;
      return 0;
  }
  """)


def broken_weave() -> str:
  return """\
  #include "klb_types.h"
  #include <stdio.h>
  #include <string.h>

  int op_weave(const char *path, KlbWeave *out) {
      FILE *f = fopen(path, "r");
      if (!f) return -1;
      memset(out, 0, sizeof *out);
      char line[512];
      while (fgets(line, sizeof line, f)) {
          if (line[0] == '#') continue;
          char tag[16];
          if (sscanf(line, "%15s", tag) != 1) continue;
          if (strcmp(tag, "LCK") == 0 && out->n_gate < KLB_MAX_STEPS) {
              KlbGateEvt *e = &out->gate[out->n_gate++];
              sscanf(line, "%*s %lld %31s %31s", (long long *)&e->ts, e->actor, e->gate);
              char op[16];
              sscanf(line, "%*s %*s %*s %*s %15s", op);
              e->is_wait = 0;
              e->is_rel = 0;
          } else if (strcmp(tag, "TMR") == 0) {
              char op[16];
              sscanf(line, "%*s %lld %31s %*s %15s %lld", (long long *)&out->miss_ts, out->missed, op, (long long *)&out->miss_ts);
          }
      }
      fclose(f);
      return 0;
  }
  """


def oracle_weave() -> str:
  return """\
  #include "klb_types.h"
  #include <stdio.h>
  #include <string.h>

  int op_weave(const char *path, KlbWeave *out) {
      FILE *f = fopen(path, "r");
      if (!f) return -1;
      memset(out, 0, sizeof *out);
      char line[512];
      while (fgets(line, sizeof line, f)) {
          if (line[0] == '#') continue;
          char tag[16];
          if (sscanf(line, "%15s", tag) != 1) continue;
          if (strcmp(tag, "LCK") == 0 && out->n_gate < KLB_MAX_STEPS) {
              KlbGateEvt *e = &out->gate[out->n_gate++];
              sscanf(line, "%*s %lld %31s %31s", (long long *)&e->ts, e->actor, e->gate);
              char op[16];
              sscanf(line, "%*s %*s %*s %*s %15s", op);
              e->is_wait = (strcmp(op, "WAIT") == 0);
              e->is_rel = (strcmp(op, "REL") == 0);
          } else if (strcmp(tag, "TSW") == 0 && out->n_switch < KLB_MAX_STEPS) {
              KlbSwitchEvt *s = &out->sw[out->n_switch++];
              sscanf(line, "%*s %lld %31s %31s", (long long *)&s->ts, s->prev, s->next);
          } else if (strcmp(tag, "TMR") == 0) {
              char op[16];
              char who[32];
              int64_t ts, dl;
              sscanf(line, "%*s %lld %31s %*s %15s %lld", (long long *)&ts, who, op, (long long *)&dl);
              if (strcmp(op, "EXP") == 0) {
                  strncpy(out->missed, who, 31);
                  out->miss_ts = ts;
              }
          }
      }
      fclose(f);
      return 0;
  }
  """


def broken_latch() -> str:
  return """\
  #include "klb_types.h"
  #include <string.h>

  int op_latch(const KlbWeave *w, KlbLatch *out) {
      memset(out, 0, sizeof *out);
      out->at_ts = w->miss_ts;
      for (int i = 0; i < w->n_gate; i++) {
          const KlbGateEvt *e = &w->gate[i];
          if (!e->is_wait) {
              int gi = 0;
              strncpy(out->holder[gi], e->actor, 31);
          }
      }
      if (w->n_switch > 0) {
          strncpy(out->running, w->sw[w->n_switch - 1].next, 31);
      }
      return 0;
  }
  """


def oracle_latch() -> str:
  return """\
  #include "klb_types.h"
  #include <string.h>

  static int gate_index(const char *gate, char gates[][32], int *n) {
      for (int i = 0; i < *n; i++) if (strcmp(gates[i], gate) == 0) return i;
      if (*n < KLB_MAX_GATES) {
          strncpy(gates[*n], gate, 31);
          return (*n)++;
      }
      return 0;
  }

  int op_latch(const KlbWeave *w, KlbLatch *out) {
      memset(out, 0, sizeof *out);
      char gates[KLB_MAX_GATES][32];
      char holders[KLB_MAX_GATES][32];
      int n_gates = 0;
      char running[32] = "";
      char wait_gate[32] = "";
      int order[KLB_MAX_STEPS];
      int n_order = 0;
      for (int i = 0; i < w->n_gate; i++) {
          if (w->gate[i].ts <= w->miss_ts) order[n_order++] = i;
      }
      for (int a = 1; a < n_order; a++) {
          int key = order[a];
          int64_t ts = w->gate[key].ts;
          int b = a - 1;
          while (b >= 0 && w->gate[order[b]].ts > ts) {
              order[b + 1] = order[b];
              b--;
          }
          order[b + 1] = key;
      }
      for (int oi = 0; oi < n_order; oi++) {
          const KlbGateEvt *e = &w->gate[order[oi]];
          int gi = gate_index(e->gate, gates, &n_gates);
          if (e->is_wait) {
              if (strcmp(e->actor, w->missed) == 0) strncpy(wait_gate, e->gate, 31);
              continue;
          }
          if (e->is_rel) {
              holders[gi][0] = '\\0';
              continue;
          }
          strncpy(holders[gi], e->actor, 31);
      }
      for (int si = 0; si < w->n_switch; si++) {
          if (w->sw[si].ts <= w->miss_ts) strncpy(running, w->sw[si].next, 31);
      }
      if (wait_gate[0]) {
          int gi = gate_index(wait_gate, gates, &n_gates);
          strncpy(out->holder[0], holders[gi], 31);
      }
      strncpy(out->running, running, 31);
      out->at_ts = w->miss_ts;
      return 0;
  }
  """


def broken_span() -> str:
  return """\
  #include "klb_types.h"
  #include <string.h>

  int op_span(const KlbLatch *l, const char *tgt, char chain[3][32]) {
      strncpy(chain[0], tgt, 31);
      strncpy(chain[1], l->holder[0], 31);
      strncpy(chain[2], l->holder[0], 31);
      (void)l->running;
      return 0;
  }
  """


def oracle_span() -> str:
  return """\
  #include "klb_types.h"
  #include <string.h>

  int op_span(const KlbLatch *l, const char *tgt, char chain[3][32]) {
      strncpy(chain[0], tgt, 31);
      strncpy(chain[1], l->holder[0], 31);
      strncpy(chain[2], l->running, 31);
      return 0;
  }
  """


def broken_lift() -> str:
  return """\
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>

  int op_lift(const char *cfg, const char *tgt, int *ceilings, int cap) {
      (void)tgt;
      FILE *f = fopen(cfg, "r");
      if (!f) return -1;
      char line[256];
      char section[64] = "";
      int idx = 0;
      int min_band = 9999;
      while (fgets(line, sizeof line, f) && idx < cap) {
          if (line[0] == '[') {
              char *end = strchr(line, ']');
              if (!end) continue;
              *end = '\\0';
              strncpy(section, line + 1, sizeof section - 1);
              continue;
          }
          if (strcmp(section, "actors") == 0) {
              char key[64], val[64];
              if (sscanf(line, " %63[^= ] = %63s", key, val) == 2) {
                  char *dot = strchr(key, '.');
                  if (dot && strcmp(dot + 1, "band") == 0) {
                      int band = atoi(val);
                      if (band < min_band) min_band = band;
                      ceilings[idx++] = band;
                  }
              }
          }
      }
      fclose(f);
      int n_gate = 0;
      f = fopen(cfg, "r");
      section[0] = '\\0';
      while (f && fgets(line, sizeof line, f)) {
          if (line[0] == '[') {
              char *end = strchr(line, ']');
              if (!end) continue;
              *end = '\\0';
              strncpy(section, line + 1, sizeof section - 1);
          } else if (strcmp(section, "gates") == 0) {
              char key[64], val[64];
              if (sscanf(line, " %63[^= ] = %63s", key, val) == 2) {
                  char *dot = strchr(key, '.');
                  if (dot && strcmp(dot + 1, "present") == 0) n_gate++;
              }
          }
      }
      if (f) fclose(f);
      for (int i = 0; i < n_gate && i < cap; i++) ceilings[i] = min_band;
      return n_gate;
  }
  """


def oracle_lift() -> str:
  return """\
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>

  int op_lift(const char *cfg, const char *tgt, int *ceilings, int cap) {
      int wait_band = 0;
      FILE *f = fopen(cfg, "r");
      if (!f) return -1;
      char line[256];
      char section[64] = "";
      int n_gate = 0;
      while (fgets(line, sizeof line, f)) {
          if (line[0] == '[') {
              char *end = strchr(line, ']');
              if (!end) continue;
              *end = '\\0';
              strncpy(section, line + 1, sizeof section - 1);
              continue;
          }
          char key[64], val[64];
          if (sscanf(line, " %63[^= ] = %63s", key, val) != 2) continue;
          if (strcmp(section, "actors") == 0) {
              char *dot = strchr(key, '.');
              if (!dot) continue;
              *dot = '\\0';
              if (strcmp(key, tgt) == 0 && strcmp(dot + 1, "band") == 0) wait_band = atoi(val);
          } else if (strcmp(section, "gates") == 0) {
              char key[64], val[64];
              if (sscanf(line, " %63[^= ] = %63s", key, val) != 2) continue;
              char *dot = strchr(key, '.');
              if (dot && strcmp(dot + 1, "present") == 0) n_gate++;
          }
      }
      fclose(f);
      for (int i = 0; i < n_gate && i < cap; i++) ceilings[i] = wait_band;
      return n_gate;
  }
  """


def broken_stage_a() -> str:
  return """\
  #include "klb_types.h"
  #include <string.h>

  int op_weave(const char *path, KlbWeave *out);
  int op_latch(const KlbWeave *w, KlbLatch *out);

  int stage_a(const char *trace, KlbWeave *w, KlbLatch *l, char missed[32]) {
      if (op_weave(trace, w) != 0) return -1;
      KlbWeave snap = *w;
      snap.miss_ts = 0;
      if (op_latch(&snap, l) != 0) return -1;
      strncpy(missed, w->missed, 31);
      return 0;
  }
  """


def oracle_stage_a() -> str:
  return """\
  #include "klb_types.h"
  #include <string.h>

  int op_weave(const char *path, KlbWeave *out);
  int op_latch(const KlbWeave *w, KlbLatch *out);

  int stage_a(const char *trace, KlbWeave *w, KlbLatch *l, char missed[32]) {
      if (op_weave(trace, w) != 0) return -1;
      if (op_latch(w, l) != 0) return -1;
      strncpy(missed, w->missed, 31);
      return 0;
  }
  """


def klreplay_main_c() -> str:
  return """\
  #include "klb_sim.h"
  #include "klb_fmt.h"
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>

  static int parse_ceilings(const char *blob, const char *sid, char gates[][32], int ceilings[], int cap) {
      char needle[128];
      snprintf(needle, sizeof needle, "\\"%s\\"", sid);
      const char *pos = strstr(blob, needle);
      if (!pos) return -1;
      const char *cpos = strstr(pos, "\\"ceilings\\"");
      if (!cpos) return -1;
      const char *start = strchr(cpos, '{');
      const char *end = strchr(start, '}');
      if (!start || !end) return -1;
      int n = 0;
      const char *p = start + 1;
      while (p < end && n < cap) {
          p = strchr(p, '"');
          if (!p || p >= end) break;
          p++;
          char key[32];
          int ki = 0;
          while (*p && *p != '"' && ki + 1 < (int)sizeof key) key[ki++] = *p++;
          key[ki] = '\\0';
          p = strchr(p, ':');
          if (!p || p >= end) break;
          p++;
          while (*p == ' ') p++;
          ceilings[n] = atoi(p);
          strncpy(gates[n], key, 31);
          n++;
          p++;
      }
      return n;
  }

  int main(int argc, char **argv) {
      const char *cfg = NULL;
      const char *trace = NULL;
      const char *analysis = NULL;
      const char *sid = NULL;
      for (int i = 1; i < argc; i++) {
          if (strcmp(argv[i], "--cfg") == 0 && i + 1 < argc) cfg = argv[++i];
          else if (strcmp(argv[i], "--trace") == 0 && i + 1 < argc) trace = argv[++i];
          else if (strcmp(argv[i], "--analysis") == 0 && i + 1 < argc) analysis = argv[++i];
          else if (strcmp(argv[i], "--scenario") == 0 && i + 1 < argc) sid = argv[++i];
      }
      if (!cfg || !trace || !analysis || !sid) return 2;
      FILE *af = fopen(analysis, "r");
      if (!af) return 1;
      char blob[65536];
      size_t n = fread(blob, 1, sizeof blob - 1, af);
      blob[n] = '\\0';
      fclose(af);
      char gates[8][32];
      int ceilings[8];
      int n_ceil = parse_ceilings(blob, sid, gates, ceilings, 8);
      if (n_ceil < 1) return 1;
      KlbReplayResult res;
      if (klb_replay_scenario(cfg, trace, gates, ceilings, n_ceil, &res) != 0) return 1;
      printf("{\\"misses\\": %d}\\n", res.misses);
      return 0;
  }
  """


def write_probe_sources() -> None:
  w("environment/kern/a7/weave.c", broken_weave())
  w("environment/kern/a7/hash.c", """\
  #include <stdint.h>
  #include <string.h>

  uint32_t row_fingerprint(const char *s) {
      uint32_t h = 2166136261u;
      for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
          h ^= *p;
          h *= 16777619u;
      }
      return h;
  }
  """)

  w("environment/kern/a7/filter.c", """\
  #include "klb_types.h"
  #include <string.h>

  int filter_gate_rows(KlbWeave *w) {
      int out = 0;
      for (int i = 0; i < w->n_gate; i++) {
          if (!w->gate[i].is_wait) {
              w->gate[out++] = w->gate[i];
          }
      }
      w->n_gate = out;
      return 0;
  }
  """)

  w("environment/relay/m3/latch.c", broken_latch())
  w("environment/relay/m3/shadow.c", """\
  #include "klb_types.h"
  #include <stdio.h>

  void dump_shadow(const KlbLatch *l) {
      if (!l) return;
      fprintf(stderr, "shadow running=%s holder=%s\\n", l->running, l->holder[0]);
  }
  """)

  w("environment/span/q9/span.c", broken_span())
  w("environment/span/q9/ring.c", """\
  #include <string.h>
  #define RING_CAP 64
  static char ring[RING_CAP][128];
  static int rhead;

  void ring_push(const char *msg) {
      if (rhead < RING_CAP) strncpy(ring[rhead++], msg, 127);
  }
  """)

  w("environment/lift/w2/lift.c", broken_lift())

  w("environment/src/probe/stage_a.c", broken_stage_a())

  w("environment/src/probe/stage_b.c", """\
  #include "klb_types.h"

  int op_span(const KlbLatch *l, const char *tgt, char chain[3][32]);
  int op_lift(const char *cfg, const char *tgt, int *ceilings, int cap);

  int stage_b(const char *cfg, const KlbLatch *l, const char *tgt, char chain[3][32], int *ceilings, int *n_ceil) {
      if (op_span(l, tgt, chain) != 0) return -1;
      *n_ceil = op_lift(cfg, tgt, ceilings, 8);
      return 0;
  }
  """)

  w("environment/src/probe/main.c", """\
  #include "klb_types.h"
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>

  int stage_a(const char *trace, KlbWeave *w, KlbLatch *l, char missed[32]);
  int stage_b(const char *cfg, const KlbLatch *l, const char *missed, char chain[3][32], int *ceilings, int *n_ceil);

  static void write_json(FILE *out, const char *sid, const char *missed, char chain[3][32], int *ceilings, int n_ceil, const char *gates[], int n_gate) {
      fprintf(out, "    \\"%s\\": {\\n", sid);
      fprintf(out, "      \\"missed_deadline_task\\": \\"%s\\",\\n", missed);
      fprintf(out, "      \\"chain\\": [\\"%s\\", \\"%s\\", \\"%s\\"],\\n", chain[0], chain[1], chain[2]);
      fprintf(out, "      \\"ceilings\\": {");
      for (int i = 0; i < n_gate; i++) {
          int v = (i < n_ceil) ? ceilings[i] : 0;
          fprintf(out, "%s\\"%s\\": %d", i ? ", " : "", gates[i], v);
      }
      fprintf(out, "}\\n    }");
  }

  int main(int argc, char **argv) {
      const char *manifest = NULL;
      const char *outpath = NULL;
      for (int i = 1; i < argc; i++) {
          if (strcmp(argv[i], "--manifest") == 0 && i + 1 < argc) manifest = argv[++i];
          else if (strcmp(argv[i], "--out") == 0 && i + 1 < argc) outpath = argv[++i];
      }
      if (!manifest || !outpath) return 2;
      FILE *mf = fopen(manifest, "r");
      if (!mf) return 1;
      char line[512];
      FILE *out = fopen(outpath, "w");
      if (!out) { fclose(mf); return 1; }
      fprintf(out, "{\\n  \\"version\\": 1,\\n  \\"scenarios\\": {\\n");
      int first = 1;
      while (fgets(line, sizeof line, mf)) {
          char sid[64], cfg[256], trace[256];
          if (sscanf(line, " %63s %255s %255s", sid, cfg, trace) != 3) continue;
          KlbWeave w;
          KlbLatch l;
          char missed[32];
          char chain[3][32];
          int ceilings[8];
          int n_ceil = 0;
          if (stage_a(trace, &w, &l, missed) != 0) continue;
          if (stage_b(cfg, &l, missed, chain, ceilings, &n_ceil) != 0) continue;
          char *gates[8];
          int n_gate = 0;
          FILE *cf = fopen(cfg, "r");
          char cl[256], section[64] = "";
          while (cf && fgets(cl, sizeof cl, cf)) {
              if (cl[0] == '[') {
                  char *end = strchr(cl, ']');
                  if (!end) continue;
                  *end = '\\0';
                  strncpy(section, cl + 1, 63);
          } else if (strcmp(section, "gates") == 0) {
              char key[64], val[64];
              if (sscanf(cl, " %63[^= ] = %63s", key, val) != 2) continue;
              char *dot = strchr(key, '.');
              if (!dot) continue;
              *dot = '\\0';
              if (strcmp(dot + 1, "present") == 0) {
                  static char gatebuf[8][32];
                  strncpy(gatebuf[n_gate], key, 31);
                  gates[n_gate] = gatebuf[n_gate];
                  n_gate++;
              }
          }
          }
          if (cf) fclose(cf);
          if (!first) fprintf(out, ",\\n");
          first = 0;
          write_json(out, sid, missed, chain, ceilings, n_ceil, (const char **)gates, n_gate);
      }
      fprintf(out, "\\n  }\\n}\\n");
      fclose(out);
      fclose(mf);
      return 0;
  }
  """)


def write_packaging() -> None:
  w("environment/packaging/klreplay_main.c", klreplay_main_c())


def write_configs() -> None:
  manifest_lines = []
  for sid in SCENARIOS:
    manifest_lines.append(f"{sid} {OPT}/config/{sid}.toml {OPT}/traces/{sid}.evt")
  w("environment/config/manifest.json", json.dumps({"version": 1, "rows": list(SCENARIOS.keys())}, indent=2) + "\n")
  w("environment/config/manifest.txt", "\n".join(manifest_lines) + "\n")

  for sid, spec in SCENARIOS.items():
    lines = ["[meta]", f'id = "{sid}"', "", "[actors]"]
    for actor, info in spec["tasks"].items():
      lines.append(f"{actor}.band = {info['prio']}")
      lines.append(f"{actor}.period_us = {info['period_us']}")
    lines.append("")
    lines.append("[gates]")
    for g in spec["locks"]:
      lines.append(f"{g}.present = 1")
    w(f"environment/config/{sid}.toml", "\n".join(lines) + "\n")


def write_traces() -> None:
  for sid, body in TRACES.items():
    w(f"environment/traces/{sid}.evt", body)


def write_docs() -> None:
  w("environment/docs/event_layout.txt", """\
  klb evt v1 — one record per line, # comments allowed.

  TSW <ts_ns> <prev_actor> <next_actor>
  LCK <ts_ns> <actor> <gate_id> ACQ|REL|WAIT
  WUP <ts_ns> <src_actor> <dst_actor>
  TMR <ts_ns> <actor> <job_id> ARM|EXP <deadline_ns>
  JOB <ts_ns> <actor> START|END

  WAIT marks an actor blocked on a gate without taking ownership.
  EXP marks a release window observation used to anchor reconstruction.
  """)

  w("environment/docs/analysis_schema.txt", """\
  /output/analysis.json version 1

  scenarios.<manifest_id>.missed_deadline_task — actor id string
  scenarios.<manifest_id>.chain — array of exactly 3 actor id strings in fixed order:
    [0] same actor as missed_deadline_task (waiter blocked at the expiry anchor instant)
    [1] gate holder blocking index 0 at that anchor instant
    [2] runnable actor on-CPU at that anchor instant
  scenarios.<manifest_id>.ceilings — map of gate id to integer band (exact waiter band per gate)
  """)

  w("environment/docs/replay_cli.txt", """\
  /opt/kernlab/bin/klreplay per-scenario flags:
    --cfg <toml> --trace <evt> --analysis <json> --scenario <manifest_id>

  Successful stdout is one JSON object only, for example {"misses": 0}.
  Do not prefix stdout with labels or scenario ids.
  """)

  w("environment/docs/set_catalog.txt", """\
  Per-case TOML encodes actor bands (higher integer = more urgent) and gate ids.
  """)

  w("environment/scripts/smoke.sh", """\
  #!/bin/sh
  set -e
  /opt/kernlab/bin/kernprobe --manifest /opt/kernlab/config/manifest.txt --out /tmp/smoke.json
  test -s /tmp/smoke.json
  """)


def write_makefile() -> None:
  w("environment/Makefile", """\
  CC = gcc
  CFLAGS = -Wall -Wextra -std=c11 -Iinclude
  LDFLAGS =

  SIM_OBJS = src/sim/core.o src/sim/queue.o src/sim/lock.o src/sim/deadline.o src/sim/replay.o src/sim/util.o
  PROBE_OBJS = src/probe/main.o src/probe/stage_a.o src/probe/stage_b.o kern/a7/weave.o kern/a7/hash.o relay/m3/latch.o relay/m3/shadow.o span/q9/span.o span/q9/ring.o lift/w2/lift.o $(SIM_OBJS)

  all: kernprobe

  kernprobe: $(PROBE_OBJS)
  \t$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

  klreplay-vendor: $(SIM_OBJS)
  \t@test -f /tmp/klreplay_main.c
  \t$(CC) $(CFLAGS) -o klreplay /tmp/klreplay_main.c $(SIM_OBJS) $(LDFLAGS)

  clean:
  \trm -f kernprobe klreplay $(SIM_OBJS) $(PROBE_OBJS)

  .PHONY: all clean klreplay-vendor
  """)


def write_dockerfile() -> None:
  w("environment/Dockerfile", """\
  # syntax=docker/dockerfile:1

  # Canonical GCC toolchain image (C/C++ tasks; agents compile in-container).
  FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

  LABEL org.opencontainers.image.source="terminal-bench-3"
  LABEL org.opencontainers.image.version="1.0.0"
  LABEL org.opencontainers.image.licenses="MIT"

  # Agent runtime requires tmux and asciinema before any other setup.
  RUN apt-get update \\
      && apt-get install -y --no-install-recommends tmux asciinema \\
      && rm -rf /var/lib/apt/lists/*

  ENV TERM=xterm-256color

  RUN tmux -V \\
      && asciinema --version \\
      && tmux new-session -d -s _smoke \\
      && tmux has-session -t _smoke \\
      && tmux kill-session -t _smoke

  RUN apt-get update \\
      && apt-get install -y --no-install-recommends \\
          bash \\
          ca-certificates \\
          coreutils \\
          procps \\
          python3 \\
          python3-pip \\
      && rm -rf /var/lib/apt/lists/*

  RUN pip3 install --no-cache-dir --break-system-packages \\
      pytest==8.4.1 \\
      pytest-json-ctrf==0.3.5

  COPY include /opt/kernlab/include
  COPY src /opt/kernlab/src
  COPY kern /opt/kernlab/kern
  COPY relay /opt/kernlab/relay
  COPY span /opt/kernlab/span
  COPY lift /opt/kernlab/lift
  COPY config /opt/kernlab/config
  COPY traces /opt/kernlab/traces
  COPY docs /opt/kernlab/docs
  COPY scripts /opt/kernlab/scripts
  COPY Makefile /opt/kernlab/Makefile
  COPY packaging/klreplay_main.c /tmp/klreplay_main.c

  RUN make -C /opt/kernlab kernprobe && make -C /opt/kernlab klreplay-vendor \\
      && mkdir -p /opt/kernlab/bin \\
      && mv /opt/kernlab/kernprobe /opt/kernlab/klreplay /opt/kernlab/bin/ \\
      && rm -f /tmp/klreplay_main.c \\
      && chmod +x /opt/kernlab/scripts/smoke.sh \\
      && /opt/kernlab/scripts/smoke.sh

  RUN tmux -V \\
      && asciinema --version \\
      && tmux new-session -d -s _smoke \\
      && tmux has-session -t _smoke \\
      && tmux kill-session -t _smoke

  WORKDIR /opt/kernlab
  ENV PATH="/opt/kernlab/bin:${PATH}"
  """)


def write_dockerignore() -> None:
  w("environment/.dockerignore", """\
  .git
  .gitignore
  **/__pycache__/
  **/*.pyc
  **/.pytest_cache/
  **/.mypy_cache/
  **/.ruff_cache/
  **/node_modules/
  **/target/
  **/dist/
  **/build/
  **/.venv/
  **/venv/
  .env
  *.log
  solution/
  tests/
  **/*.o
  kernprobe
  klreplay
  bin/
  """)


def write_task_meta() -> None:
  w("task.toml", """\
  version = "2.0"

  [metadata]
  author_name = "anonymous"
  author_email = "anonymous"
  difficulty = "hard"
  category = "scientific-computing"
  subcategories = ["tool_specific"]
  number_of_milestones = 0
  codebase_size = "small"
  languages = ["C"]
  tags = ["c", "real-time", "scheduling", "trace", "simulation", "scientific-computing"]
  expert_time_estimate_min = 240
  junior_time_estimate_min = 480

  [verifier]
  timeout_sec = 600

  [agent]
  timeout_sec = 1200

  [environment]
  allow_internet = false
  build_timeout_sec = 900
  cpus = 2
  memory_mb = 4096
  storage_mb = 10240
  """)

  w("output_contract.toml", """\
  user_visible_outputs = [
    "/output/analysis.json",
  ]

  internal_harness_files = [
    "/opt/kernlab/traces/",
  ]

  [structured_outputs.analysis]
  target = "/output/analysis.json"
  format = "json"
  instruction_checks = ["version", "scenarios", "missed_deadline_task", "chain", "ceilings"]
  """)


def write_instruction() -> None:
  w("instruction.md", """\
  Periodic release windows are slipping on several traced workloads under `/opt/kernlab/`. The probe at `/opt/kernlab/bin/kernprobe` walks `/opt/kernlab/config/manifest.txt` and writes `/output/analysis.json`, but replay proof with `/opt/kernlab/bin/klreplay` still fails and the analysis rows do not line up with the captures.

  Rebuild what is needed under `/opt/kernlab/`, rerun the probe, and get a clean replay pass on every manifest row. Output field names and replay stdout expectations are documented under `/opt/kernlab/docs/`.

  Deliver `/output/analysis.json` at version `1` with one entry per manifest id under `scenarios`. Each row includes `missed_deadline_task`, a `chain` of 3 actor ids, and `ceilings` as defined in `/opt/kernlab/docs/analysis_schema.txt`.
  """)


def write_tests() -> None:
  ref_cases = {sid: {"chain": spec["chain"], "ceilings": spec["ceilings"], "missed": spec["missed"]} for sid, spec in SCENARIOS.items()}
  w("tests/chain_ref.py", f"CASES = {json.dumps(ref_cases, indent=2)}\n")

  w("tests/test_outputs.py", """\
  \"\"\"Verifier for kernlab analysis outputs.\"\"\"

  import ast
  import json
  import subprocess

  import pytest
  from pathlib import Path

  OUT = Path("/output/analysis.json")
  MANIFEST = Path("/opt/kernlab/config/manifest.txt")
  PROBE = Path("/opt/kernlab/bin/kernprobe")
  REF = Path(__file__).resolve().parent / "chain_ref.py"


  def _load_cases():
      mod = ast.parse(REF.read_text(encoding="utf-8"))
      for node in mod.body:
          if isinstance(node, ast.Assign):
              for target in node.targets:
                  if isinstance(target, ast.Name) and target.id == "CASES":
                      return ast.literal_eval(node.value)
      raise RuntimeError("CASES missing from chain_ref.py")


  CASES = _load_cases()


  def _scenario_ids():
      rows = []
      for line in MANIFEST.read_text(encoding="utf-8").splitlines():
          parts = line.split()
          if len(parts) >= 1:
              rows.append(parts[0])
      return rows


  SCENARIOS = _scenario_ids()


  def _load_doc():
      assert OUT.is_file(), f"missing {OUT}"
      doc = json.loads(OUT.read_text(encoding="utf-8"))
      assert doc.get("version") == 1
      assert isinstance(doc.get("scenarios"), dict)
      return doc


  def _replay(sid: str) -> int:
      _load_doc()
      proc = subprocess.run(
          [
              "/opt/kernlab/bin/klreplay",
              "--cfg",
              f"/opt/kernlab/config/{sid}.toml",
              "--trace",
              f"/opt/kernlab/traces/{sid}.evt",
              "--analysis",
              str(OUT),
              "--scenario",
              sid,
          ],
          capture_output=True,
          text=True,
          check=False,
      )
      if proc.returncode != 0 or not proc.stdout.strip():
          return 1
      row = json.loads(proc.stdout.strip())
      return int(row.get("misses", 1))


  def test_probe_regenerates_analysis():
      \"\"\"kernprobe must rebuild analysis.json from the compiled probe binary.\"\"\"
      assert PROBE.is_file(), f"missing {PROBE}"
      if OUT.exists():
          OUT.unlink()
      OUT.parent.mkdir(parents=True, exist_ok=True)
      proc = subprocess.run(
          [
              str(PROBE),
              "--manifest",
              str(MANIFEST),
              "--out",
              str(OUT),
          ],
          capture_output=True,
          text=True,
          check=False,
      )
      assert proc.returncode == 0, proc.stderr or proc.stdout
      doc = _load_doc()
      for sid in SCENARIOS:
          assert sid in doc["scenarios"]


  def test_h4_schema_bundle():
      \"\"\"analysis.json exposes version and every manifest scenario.\"\"\"
      doc = _load_doc()
      for sid in SCENARIOS:
          assert sid in doc["scenarios"]
          row = doc["scenarios"][sid]
          assert isinstance(row.get("missed_deadline_task"), str)
          assert isinstance(row.get("chain"), list)
          assert len(row["chain"]) == 3
          assert isinstance(row.get("ceilings"), dict)


  @pytest.mark.parametrize("sid", sorted(CASES.keys()))
  def test_chain_matches_reference(sid):
      \"\"\"Each manifest row reports the expected blocking band.\"\"\"
      doc = _load_doc()
      want = CASES[sid]
      row = doc["scenarios"][sid]
      assert row["missed_deadline_task"] == want["missed"]
      assert row["chain"] == want["chain"]
      assert row["ceilings"] == want["ceilings"]


  @pytest.mark.parametrize("sid", sorted(CASES.keys()))
  def test_replay_zero_misses(sid):
      \"\"\"Submitted ceilings pass deterministic replay proof.\"\"\"
      assert _replay(sid) == 0
  """)

  w("tests/test.sh", """\
  #!/bin/bash

  # Verifier dependencies are installed in environment/Dockerfile.

  mkdir -p /logs/verifier

  if [ "$PWD" = "/" ]; then
      echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
      echo 0 > /logs/verifier/reward.txt
      exit 1
  fi

  python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
    --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

  if [ $? -eq 0 ]; then
      echo 1 > /logs/verifier/reward.txt
  else
      echo 0 > /logs/verifier/reward.txt
  fi
  """)


def write_solution() -> None:
  w("solution/solve.sh", f"""\
  #!/usr/bin/env bash
  set -euo pipefail

  cd /opt/kernlab

  cat > kern/a7/weave.c <<'CEOF'
  {oracle_weave().strip()}
  CEOF

  cat > relay/m3/latch.c <<'CEOF'
  {oracle_latch().strip()}
  CEOF

  cat > span/q9/span.c <<'CEOF'
  {oracle_span().strip()}
  CEOF

  cat > lift/w2/lift.c <<'CEOF'
  {oracle_lift().strip()}
  CEOF

  cat > src/probe/stage_a.c <<'CEOF'
  {oracle_stage_a().strip()}
  CEOF

  make clean
  make all
  mkdir -p bin
  mv -f kernprobe bin/

  mkdir -p /output
  /opt/kernlab/bin/kernprobe --manifest /opt/kernlab/config/manifest.txt --out /output/analysis.json
  """)


if __name__ == "__main__":
  main()
