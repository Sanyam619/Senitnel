pub fn epoch_after(ckpt: u32, tip: u32, resume: u8) -> u32 {
    crate::slot_v::slot_v(ckpt, tip, resume)
}
