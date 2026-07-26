# Thermal handoff policy
# Graded advances bind contact / reduction / dt tokens from
# /app/config/profiles/*.toml for the active profile_id.
# After accept: handoff.accept present, trial_pref.live absent;
# prep_eval must not rematerialize trial_pref from trial_pref.seed.
authority = "profile"
scratch = "trial_pref.live"
accept_receipt = "handoff.accept"
