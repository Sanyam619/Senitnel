pub fn J1_seq(seqs: &[i32]) -> bool {
    seqs.windows(2).all(|w| w[1] >= w[0])
}
