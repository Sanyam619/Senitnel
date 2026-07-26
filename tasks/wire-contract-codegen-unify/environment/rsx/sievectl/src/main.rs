use core::{rows_to_json, sieve_b};

fn main() {
    let reg = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "/app/data/registry".to_string());
    let pin = std::env::args()
        .nth(2)
        .unwrap_or_else(|| "/app/rsx/pins.toml".to_string());
    match sieve_b(&reg, &pin) {
        Ok(rows) => {
            println!("{}", rows_to_json(&rows));
        }
        Err(e) => {
            eprintln!("sievectl: {}", e);
            std::process::exit(1);
        }
    }
}
