use crate::spec::SpecX;
use proc_macro2::TokenStream;
use quote::quote;

include!(concat!(env!("OUT_DIR"), "/lane_bind.rs"));

/// Expanded token payload handed to the surface crate.
pub struct BundleY {
    body: TokenStream,
}

impl BundleY {
    pub fn into_tokens(self) -> TokenStream {
        self.body
    }
}

/// Builds the expanded token bundle used by downstream hosts.
pub fn knit_a(spec: &SpecX) -> BundleY {
    // Live expand polarity is correct; lane enablement comes from bind_k.
    let use_a = LANE_X_ON && spec.a != 0;
    let use_b = LANE_Y_ON && spec.b != 0;

    let vt_entries: Vec<TokenStream> = {
        let mut rows = vec![quote! { b"MG_CORE\0" }];
        if use_a {
            rows.push(quote! { b"MG_LANE_X\0" });
        }
        if use_b {
            rows.push(quote! { b"MG_LANE_Y\0" });
        }
        rows
    };

    let vt_block = quote! {
        static __MG_VT: &[&[u8]] = &[#(#vt_entries),*];
    };

    let lane_a = if use_a {
        quote! {
            #[no_mangle]
            pub extern "C" fn mg_lane_x_open() -> i32 {
                p2::gated_x()
            }
        }
    } else {
        quote! {}
    };

    let lane_b = if use_b {
        quote! {
            #[no_mangle]
            pub extern "C" fn mg_lane_y_open() -> i32 {
                0x4d02
            }
        }
    } else {
        quote! {}
    };

    let core = quote! {
        #[no_mangle]
        pub extern "C" fn mg_core_open() -> i32 {
            0x4d01
        }

        #[no_mangle]
        pub extern "C" fn mg_vt_count() -> i32 {
            __MG_VT.len() as i32
        }

        #[no_mangle]
        pub extern "C" fn mg_vt_at(idx: i32) -> *const u8 {
            if idx < 0 || (idx as usize) >= __MG_VT.len() {
                return core::ptr::null();
            }
            __MG_VT[idx as usize].as_ptr()
        }
    };

    BundleY {
        body: quote! {
            #vt_block
            #core
            #lane_a
            #lane_b
        },
    }
}
