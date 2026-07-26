mod delta_impl {
    include!(concat!(env!("CARGO_MANIFEST_DIR"), "/src/", "delta_", "q.rs"));
}
pub mod desk;
pub mod dial;
mod mark_impl {
    include!(concat!(env!("CARGO_MANIFEST_DIR"), "/src/", "mark_", "w.rs"));
}
mod op_impl {
    include!(concat!(env!("CARGO_MANIFEST_DIR"), "/src/", "op_", "v.rs"));
}
