use crate::RowR;

/// Signature-surface skim: passes any row that carries a non-empty id token.
/// Ignores the mark list and the freshness bounds.
pub fn skim_pol(a: &RowR) -> bool {
    !a.id.is_empty()
}
