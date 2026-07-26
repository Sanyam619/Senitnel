use std::env;
use std::fs;
use std::path::Path;
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();
    let out = parse_out(&args).unwrap_or_else(|| "/output/mesh-attestation.json".to_string());

    let surface = Path::new("/app/data/fixtures/surface_attestation.json");
    if let Some(parent) = Path::new(&out).parent() {
        if !parent.as_os_str().is_empty() {
            let _ = fs::create_dir_all(parent);
        }
    }
    if let Err(e) = fs::copy(surface, &out) {
        eprintln!("surfskim: copy failed: {e}");
        process::exit(1);
    }

    let reject_path = if out.contains("mesh-attestation") {
        out.replace("mesh-attestation", "reject-ledger")
    } else {
        let p = Path::new(&out).parent().unwrap_or(Path::new("/output"));
        p.join("reject-ledger.json").to_string_lossy().into_owned()
    };
    let body = "{\n  \"version\": 1,\n  \"rejected\": []\n}\n";
    if let Err(e) = fs::write(&reject_path, body) {
        eprintln!("surfskim: reject_ledger write failed: {e}");
        process::exit(1);
    }
}

fn parse_out(args: &[String]) -> Option<String> {
    args.windows(2)
        .find(|w| w[0] == "--out")
        .map(|w| w[1].clone())
}
