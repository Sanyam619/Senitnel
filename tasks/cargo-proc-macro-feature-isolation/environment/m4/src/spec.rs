use syn::parse::{Parse, ParseStream};
use syn::{LitInt, Result, Token};

/// Opaque expand input carried as two integer literals.
pub struct SpecX {
    pub a: u8,
    pub b: u8,
}

impl Parse for SpecX {
    fn parse(input: ParseStream) -> Result<Self> {
        let a_lit: LitInt = input.parse()?;
        input.parse::<Token![,]>()?;
        let b_lit: LitInt = input.parse()?;
        let a: u8 = a_lit.base10_parse()?;
        let b: u8 = b_lit.base10_parse()?;
        Ok(SpecX { a, b })
    }
}
