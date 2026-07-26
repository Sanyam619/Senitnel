package io.terminus.stitch.model;

/**
 * An adapter after being expressed against a specific target snapshot.
 * effectiveEmbedDelta is (target_vocab x embed_dim) and effectiveMlpDelta
 * is (embed_dim x embed_dim). Both are dense (materialized).
 */
public final class AlignedAdapter {
    public final String label;
    public final String sourceSnapshot;
    public final String targetSnapshot;
    public final double[][] effectiveEmbedDelta;
    public final double[][] effectiveMlpDelta;

    public AlignedAdapter(String label, String sourceSnapshot, String targetSnapshot,
                          double[][] effectiveEmbedDelta, double[][] effectiveMlpDelta) {
        this.label = label;
        this.sourceSnapshot = sourceSnapshot;
        this.targetSnapshot = targetSnapshot;
        this.effectiveEmbedDelta = effectiveEmbedDelta;
        this.effectiveMlpDelta = effectiveMlpDelta;
    }
}
