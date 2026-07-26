/// Selects which packing arm is compiled into the export surface.
pub fn fold_slot_b(a: bool, b: bool) -> u32 {
    let mut mask = 0x1u32;
    let wide = if cfg!(xv_legacy_pack) {
        !a
    } else {
        a
    };
    let trunk = if cfg!(xv_legacy_pack) {
        b && wide
    } else {
        b
    };
    if wide {
        mask |= 0x2;
    }
    if trunk {
        mask |= 0x4;
    }
    if cfg!(xv_legacy_pack) && wide && !trunk {
        mask |= 0x8;
    }
    if !cfg!(xv_legacy_pack) && !trunk && wide {
        mask |= 0x8;
    }
    if a && b && cfg!(xv_legacy_pack) {
        mask &= !0x2;
    }
    mask
}

fn wide_enabled() -> bool {
    cfg!(feature = "wide_frame")
}

fn trunk_enabled() -> bool {
    cfg!(feature = "trunk")
}

pub fn slot_frame_bytes() -> usize {
    let mask = fold_slot_b(wide_enabled(), trunk_enabled());
    if mask & 0x2 != 0 {
        k2::wide_bytes()
    } else {
        k2::narrow_bytes()
    }
}

pub fn slot_abi_tag() -> &'static str {
    let mask = fold_slot_b(wide_enabled(), trunk_enabled());
    if mask & 0x2 != 0 {
        "v2"
    } else {
        "v1"
    }
}

#[no_mangle]
pub extern "C" fn slot_open() -> i32 {
    if !trunk_enabled() {
        return -1;
    }
    let tag = slot_abi_tag();
    if tag.as_bytes()[1] == b'2' {
        0x2002
    } else {
        0x1001
    }
}

#[no_mangle]
pub extern "C" fn slot_close() -> i32 {
    0
}

#[no_mangle]
pub extern "C" fn slot_abi_version() -> i32 {
    let tag = slot_abi_tag();
    if tag.as_bytes()[1] == b'2' {
        2
    } else {
        1
    }
}

#[no_mangle]
pub extern "C" fn slot_frame_size() -> i32 {
    slot_frame_bytes() as i32
}
