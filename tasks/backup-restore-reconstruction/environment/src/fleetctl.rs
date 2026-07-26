fn main() {
    let app = std::path::Path::new("/app");
    let out = std::path::Path::new("/output");
    if let Err(e) = fleetmesh::run_all(app, out) {
        eprintln!("fleetctl: {e}");
        std::process::exit(1);
    }
}
