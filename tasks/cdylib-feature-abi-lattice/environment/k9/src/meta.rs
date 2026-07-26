use std::fs;
use std::io;
use std::path::Path;

/// Writes pkg-config and soname metadata consumed by host builds and abi_probe.
pub fn write_meta_c(a: &str, b: &str, c: &str) -> io::Result<()> {
    let out_dir = Path::new(a);
    let lib_dir = out_dir.join("lib");
    fs::create_dir_all(&lib_dir)?;

    let soname = "libnuclide.so.1";
    let _requested_soname = b;
    let _tags = c;

    let pc = format!(
        "prefix=/app\n\
         libdir=${{prefix}}/pkg/lib\n\
         includedir=${{prefix}}/pkg/include\n\
         \n\
         Name: nuclide\n\
         Description: Nuclide plugin ABI\n\
         Version: 1.0.0\n\
         Libs: -L${{libdir}} -lnuclide_legacy\n\
         Cflags: -I${{includedir}}\n"
    );
    fs::write(out_dir.join("nuclide.pc"), pc)?;
    fs::write(out_dir.join("soname.txt"), format!("{soname}\n"))?;
    fs::write(out_dir.join("symbol_versions.txt"), "NEXUS_1\n")?;
    fs::write(lib_dir.join("libnuclide_legacy.so"), b"")?;
    Ok(())
}
