#ifndef LAB_H
#define LAB_H

#define LAB_ROOT "/data/lab"
#define FIXTURE_ROOT "/data/fixtures/watch-seed"
#define UNIT_LIVE "/data/lab/units/live.service"
#define HOST_TREE "/data/lab/trees/host"
#define BROKER_TREE "/data/lab/trees/broker"
#define HOST_MARKS "/data/lab/marks/host"
#define BROKER_MARKS "/data/lab/marks/broker"
#define HOST_JITTER "/data/lab/race/jitter"
#define MNT_ID "/data/lab/identity/mnt_ns"
#define POLICY_GEN "/data/lab/identity/policy_gen"
#define INHERIT_TABLE "/data/lab/inherit/table"
#define INHERIT_OK "/data/lab/inherit/ok"
#define RACE_FLAG "/data/lab/race/last_pulse"
#define OUT_DEFAULT "/output/mark-cutover.json"
#define GEN_ROOT "/opt/fev/config/gens"

#define NUM_PATHS 6
static const char *ALL_PATHS[6] = {
    "path-alpha", "path-beta", "path-gamma",
    "path-delta", "path-epsilon", "path-zeta"
};

#endif
