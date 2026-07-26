mod cfg;
mod digest;
mod io;
mod ops;
mod query;
mod report;
mod state;

use std::{
    env,
    path::{Path, PathBuf},
};

fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let mut args: Vec<String> = env::args().skip(1).collect();
    if args.is_empty() {
        return Err("missing command".into());
    }
    let data = PathBuf::from("/app/data");
    let cfg = PathBuf::from("/app/config/l7");
    match args.remove(0).as_str() {
        "status" => ops::status(&data),
        "bind" => ops::bind(&data, &cfg),
        "sweep" => ops::sweep(&data, &cfg),
        "seal" => {
            let lane = take_flag(&args, "--lane")?;
            ops::seal(&data, &cfg, Path::new(&lane))
        }
        "query" => {
            if args.is_empty() {
                return Err("missing query mode".into());
            }
            match args.remove(0).as_str() {
                "point" => query::point(&data, &args),
                "scan" => query::scan(&data, &args),
                x => Err(format!("unknown query mode {x}")),
            }
        }
        "report" => {
            let out = take_flag(&args, "--out")?;
            report::write(&data, Path::new(&out))
        }
        x => Err(format!("unknown command {x}")),
    }
}

fn take_flag(args: &[String], name: &str) -> Result<String, String> {
    for win in args.windows(2) {
        if win[0] == name {
            return Ok(win[1].clone());
        }
    }
    Err(format!("missing {name}"))
}
