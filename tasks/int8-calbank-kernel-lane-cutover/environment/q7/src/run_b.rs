#[link(name = "kern", kind = "dylib")]
extern "C" {
    fn fold_w(a: *const u8, b: i32, c: i32) -> i32;
    fn score_u(epoch: u32, lane: i32, mixed: i32, salt: u32) -> f64;
}

pub fn pick_lane(mask: &[u8], fallback: i32) -> i32 {
    unsafe { fold_w(mask.as_ptr(), mask.len() as i32, fallback) }
}

pub fn score(epoch: u32, lane: i32, mixed: i32, salt: u32) -> f64 {
    unsafe { score_u(epoch, lane, mixed, salt) }
}
