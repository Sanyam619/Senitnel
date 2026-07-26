fn flag(args: &[String], name: &str) -> Option<String> {
    args.iter().position(|a| a == name).and_then(|i| args.get(i + 1).cloned())
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        std::process::exit(2);
    }
    if args[1] == "audit" {
        let pack = flag(&args, "--pack").unwrap_or_default();
        let out = flag(&args, "--out").unwrap_or_default();
        if pack.is_empty() || out.is_empty() {
            std::process::exit(2);
        }
        if frtl::internal::audit::run_pack(&pack, &out).is_err() {
            std::process::exit(1);
        }
        return;
    }
    std::process::exit(2);
}
