fn main() {
    let manifest = std::path::PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let kern = manifest.join("../n4");
    println!("cargo:rustc-link-search=native={}", kern.display());
    println!("cargo:rustc-link-lib=dylib=kern");
    println!("cargo:rerun-if-changed={}", kern.join("libkern.so").display());
}
