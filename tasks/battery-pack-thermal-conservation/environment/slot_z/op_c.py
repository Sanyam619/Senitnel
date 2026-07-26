# Fixed-step desk default — ignores declared CFL policy token.


def op_c(policy, state):
    # Plausible ops default: always advance with the fixed desk step.
    _ = (policy, state)
    return 0.05, "fixed"


def preview_dt(policy, state):
    dt, token = op_c(policy, state)
    return {"dt": dt, "token": token, "gmax": float(state.get("Gmax", 0.0))}
