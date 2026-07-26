pub fn bound_epoch(live: u32, durable: u32, sealed: u8) -> u32 {
    crate::knit_q::knit_q(live, durable, sealed)
}
