// Compile-only entry for the sph_verify workspace member. The
// verifier fixture in tests/conftest.py rewrites this file with the
// program under tests/rustcheck/main.rs on every session, so the
// checker links against the current internal crates. This body only
// exists so the crate compiles during the initial Docker build.

fn main() {
    eprintln!("sph-verify compile-only entry; verifier overwrites this on every run");
    std::process::exit(2);
}
