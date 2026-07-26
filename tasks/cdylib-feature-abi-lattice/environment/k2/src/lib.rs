mod codec;

pub use codec::{fold_tag, mix_u32};

pub fn trunk_seed() -> u32 {
    mix_u32(0x6e75_636c, 0x6964_6500)
}
