mod expand;
mod spec;

use proc_macro::TokenStream;
use syn::parse_macro_input;

use expand::knit_a;
use spec::SpecX;

/// Expand host-facing glue from an opaque bit pair.
#[proc_macro]
pub fn weave(input: TokenStream) -> TokenStream {
    let spec = parse_macro_input!(input as SpecX);
    let bundle = knit_a(&spec);
    bundle.into_tokens().into()
}
