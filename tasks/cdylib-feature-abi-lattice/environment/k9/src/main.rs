use k9::write_meta_c;
use std::env;
use std::process::ExitCode;

fn main() -> ExitCode {
    let mut args = env::args().skip(1);
    let out = match args.next() {
        Some(v) => v,
        None => {
            eprintln!("usage: meta_emit <out_dir> <soname> <tags_csv>");
            return ExitCode::from(2);
        }
    };
    let soname = args.next().unwrap_or_else(|| "libnuclide.so.2".into());
    let tags = args.next().unwrap_or_else(|| "NEXUS_1,NEXUS_2".into());
    match write_meta_c(&out, &soname, &tags) {
        Ok(()) => ExitCode::SUCCESS,
        Err(err) => {
            eprintln!("meta_emit: {err}");
            ExitCode::FAILURE
        }
    }
}
