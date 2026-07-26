pub mod body;

pub fn bind_row(body: &serde_json::Value) -> String {
    let sr = &body["scope_row"];
    let labels: Vec<String> = sr["labels_matched"]
        .as_array()
        .map(|arr| {
            arr.iter()
                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                .collect()
        })
        .unwrap_or_default();
    let rows: Vec<body::TileRow> = body["suppression_rows"]
        .as_array()
        .map(|arr| {
            arr.iter()
                .map(|r| body::TileRow {
                    bound: r["bound"].as_bool().unwrap_or(false),
                    container_id: r["container_id"].as_str().unwrap_or("").to_string(),
                    pid: r["pid"].as_i64().unwrap_or(0) as i32,
                    reason: r["reason"].as_str().unwrap_or("").to_string(),
                    rule: r["rule"].as_str().unwrap_or("").to_string(),
                })
                .collect()
        })
        .unwrap_or_default();
    body::F9_bind(
        body["batch_id"].as_str().unwrap_or(""),
        body["alert_count"].as_i64().unwrap_or(0) as i32,
        &rows,
        sr["scope_match"].as_bool().unwrap_or(false),
        body["rate_ok"].as_bool().unwrap_or(false),
        body["winning_priority"].as_i64().unwrap_or(0) as i32,
        body["effective_rate_window_sec"].as_i64().unwrap_or(0) as i32,
        body["priority_floor"].as_i64().unwrap_or(0) as i32,
        body["batch_order_ok"].as_bool().unwrap_or(false),
        sr["container_id"].as_str().unwrap_or(""),
        &labels,
    )
}
