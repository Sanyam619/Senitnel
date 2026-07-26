pub fn Q5_gate(emitted: i32, limit: i32, in_window: bool) -> bool {
    !in_window || emitted <= limit
}
