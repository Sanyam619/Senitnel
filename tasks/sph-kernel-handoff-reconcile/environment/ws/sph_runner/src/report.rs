// Emits the JSON report consumed by the verifier.
//
// The writer is hand-rolled (no serde) so the runner keeps a very
// small, offline dependency surface. The output shape is documented
// in /app/docs/reconcile-schema.md.

use std::fmt::Write as _;

pub struct ScenarioRow {
    pub scenario: String,
    pub kernel_source: String,
    pub kernel_target: String,
    pub particles: usize,
    pub converged: bool,
    pub moment_zero_residual: f64,
    pub h_consistency_residual: f64,
    pub momentum_residual: f64,
    pub angular_residual: f64,
    pub gravity_virial_residual: f64,
    pub chunk_stability_delta: f64,
}

pub struct Report {
    pub schema_tag: String,
    pub scenarios: Vec<ScenarioRow>,
}

fn num(v: f64) -> String {
    if !v.is_finite() {
        return "null".to_string();
    }
    if v == 0.0 {
        return "0.0".to_string();
    }
    format!("{:.17e}", v)
}

fn quote(s: &str) -> String {
    let mut buf = String::with_capacity(s.len() + 2);
    buf.push('"');
    for c in s.chars() {
        match c {
            '"' => buf.push_str("\\\""),
            '\\' => buf.push_str("\\\\"),
            '\n' => buf.push_str("\\n"),
            '\r' => buf.push_str("\\r"),
            '\t' => buf.push_str("\\t"),
            _ => buf.push(c),
        }
    }
    buf.push('"');
    buf
}

pub fn render(report: &Report) -> String {
    let mut out = String::new();
    out.push_str("{\n");
    let _ = writeln!(out, "  \"schema_tag\": {},", quote(&report.schema_tag));
    out.push_str("  \"scenarios\": [\n");
    for (idx, row) in report.scenarios.iter().enumerate() {
        out.push_str("    {\n");
        let _ = writeln!(out, "      \"scenario\": {},", quote(&row.scenario));
        let _ = writeln!(out, "      \"kernel_source\": {},", quote(&row.kernel_source));
        let _ = writeln!(out, "      \"kernel_target\": {},", quote(&row.kernel_target));
        let _ = writeln!(out, "      \"particles\": {},", row.particles);
        let _ = writeln!(out, "      \"converged\": {},", row.converged);
        let _ = writeln!(out, "      \"moment_zero_residual\": {},", num(row.moment_zero_residual));
        let _ = writeln!(out, "      \"h_consistency_residual\": {},", num(row.h_consistency_residual));
        let _ = writeln!(out, "      \"momentum_residual\": {},", num(row.momentum_residual));
        let _ = writeln!(out, "      \"angular_residual\": {},", num(row.angular_residual));
        let _ = writeln!(out, "      \"gravity_virial_residual\": {},", num(row.gravity_virial_residual));
        let _ = writeln!(out, "      \"chunk_stability_delta\": {}", num(row.chunk_stability_delta));
        if idx + 1 == report.scenarios.len() {
            out.push_str("    }\n");
        } else {
            out.push_str("    },\n");
        }
    }
    out.push_str("  ],\n");

    let mut max_mz = 0.0f64;
    let mut max_p = 0.0f64;
    let mut max_a = 0.0f64;
    let mut max_h = 0.0f64;
    for row in &report.scenarios {
        if row.moment_zero_residual > max_mz {
            max_mz = row.moment_zero_residual;
        }
        if row.momentum_residual > max_p {
            max_p = row.momentum_residual;
        }
        if row.angular_residual > max_a {
            max_a = row.angular_residual;
        }
        if row.h_consistency_residual > max_h {
            max_h = row.h_consistency_residual;
        }
    }
    out.push_str("  \"invariants\": {\n");
    let _ = writeln!(out, "    \"max_moment_zero\": {},", num(max_mz));
    let _ = writeln!(out, "    \"max_momentum\": {},", num(max_p));
    let _ = writeln!(out, "    \"max_angular\": {},", num(max_a));
    let _ = writeln!(out, "    \"max_h_consistency\": {}", num(max_h));
    out.push_str("  }\n");
    out.push_str("}\n");
    out
}
