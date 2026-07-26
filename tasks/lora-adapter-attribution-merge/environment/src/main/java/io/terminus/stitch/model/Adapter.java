package io.terminus.stitch.model;

/**
 * Low-rank adapter in factored form. The effective embedding delta is
 * embedB @ embedA (source_vocab x embed_dim). The effective MLP delta is
 * mlpB @ mlpA (embed_dim x embed_dim).
 */
public final class Adapter {
    public final String label;
    public final String sourceSnapshot;
    public final int rank;
    public final double[][] embedA;
    public final double[][] embedB;
    public final double[][] mlpA;
    public final double[][] mlpB;

    public Adapter(String label, String sourceSnapshot, int rank,
                   double[][] embedA, double[][] embedB,
                   double[][] mlpA, double[][] mlpB) {
        this.label = label;
        this.sourceSnapshot = sourceSnapshot;
        this.rank = rank;
        this.embedA = embedA;
        this.embedB = embedB;
        this.mlpA = mlpA;
        this.mlpB = mlpB;
    }
}
