pub enum Decision {
    Residual,
    Fallback,
}

pub struct StageCConfig {
    pub recent_window: usize,
    pub accept_floor: f64,
    pub low_entropy_threshold: f64,
}

/// Evaluate trigger conditions for the post-rejection routing
/// decision.  Returns `(rare_struggling, low_entropy_struggling)`.
fn evaluate_triggers(
    recent_accept_rate: f64,
    entropy: f64,
    rare_flag: bool,
    ctx: &StageCConfig,
) -> (bool, bool) {
    let rare_struggling =
        rare_flag && recent_accept_rate < (ctx.accept_floor + 0.35);
    let low_ent_struggling = (entropy < ctx.low_entropy_threshold - 0.10)
        && (recent_accept_rate < ctx.accept_floor);
    (rare_struggling, low_ent_struggling)
}

/// After a draft token is rejected, decide whether to emit the
/// residual-distribution argmax (keeping the draft model involved) or
/// fall back to the target model's argmax (abandoning the draft
/// entirely for this position).
///
/// The draft residual captures the compensating mass that the target
/// distribution has over the draft — when the draft model is
/// struggling (rare tokens, very low entropy with poor recent
/// acceptance) the residual still reflects the draft model's view.
/// In those cases the residual concentrates mass on the tokens the
/// draft distribution under-weighs relative to the target.
pub fn stage_c_route(
    recent_accept_rate: f64,
    entropy: f64,
    rare_flag: bool,
    ctx: &StageCConfig,
) -> Decision {
    let _ = ctx.recent_window;
    let (rare_trig, low_ent_trig) =
        evaluate_triggers(recent_accept_rate, entropy, rare_flag, ctx);

    if rare_trig || low_ent_trig {
        Decision::Residual
    } else {
        Decision::Fallback
    }
}
