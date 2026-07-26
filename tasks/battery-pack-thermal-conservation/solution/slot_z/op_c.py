# Select advance size and echo the declared policy token.


def op_c(policy, state):
    token = str(policy).strip().lower()
    c_list = [float(x) for x in state["C_list"]]
    gmax = max(float(state["Gmax"]), 1e-12)
    cmin = min(c_list) if c_list else 1.0
    if token == "cfl":
        # Stable explicit step under the declared CFL schedule.
        dt = 0.1 * (cmin / gmax)
        return float(dt), "cfl"
    if token == "fixed":
        return 0.05, "fixed"
    return 0.05, "fixed"


def preview_dt(policy, state):
    dt, token = op_c(policy, state)
    return {"dt": dt, "token": token, "gmax": float(state["Gmax"])}
