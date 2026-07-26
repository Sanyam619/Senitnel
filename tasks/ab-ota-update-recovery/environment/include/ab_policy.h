#ifndef AB_POLICY_H
#define AB_POLICY_H

typedef enum {
    AB_RULE_ROLLBACK_STAGING_B = 0,
    AB_RULE_REPOINT_LIVE_B_FAIL = 1,
    AB_RULE_COMMIT_STAGING_A = 2,
    AB_RULE_ROLLBACK_LIVE_B_FAIL = 3,
    AB_RULE_HOLD = 4,
    AB_RULE_COUNT = 5,
} ab_rule_id_t;

typedef struct {
    ab_rule_id_t rule_order[AB_RULE_COUNT];
    int rule_count;
    int allow_commit;
} ab_recovery_policy_t;

int ab_policy_default(ab_recovery_policy_t *out);
int ab_policy_load(const char *path, ab_recovery_policy_t *out);
const char *ab_rule_name(ab_rule_id_t id);
int ab_rule_from_name(const char *name, ab_rule_id_t *out);

#endif
