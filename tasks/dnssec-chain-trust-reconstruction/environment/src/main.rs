mod clock; mod core; mod io; mod model; mod report;
use std::{env, path::PathBuf};
fn main(){
 let a:Vec<String>=env::args().collect(); if a.len()!=3{eprintln!("usage"); std::process::exit(2)}
 let data=io::scan::load_all(&PathBuf::from("/app/data/registry"), &PathBuf::from(&a[1])).unwrap_or_else(|e|{eprintln!("{e}"); std::process::exit(3)});
 let (v,r)=report::emit::emit_d(&data); let out=PathBuf::from(&a[2]); std::fs::create_dir_all(&out).unwrap(); std::fs::write(out.join("validation.json"),v).unwrap(); std::fs::write(out.join("replayed.json"),r).unwrap();
}
