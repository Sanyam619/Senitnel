package io.terminus.stitch.model;

import java.util.LinkedHashMap;
import java.util.Map;

/** Merged state after fusion, plus per-source deltas for attribution. */
public final class FusedState {
    public final int vocab;
    public final int embedDim;
    public double[][] fullEmbedDelta;
    public double[][] fullMlpDelta;
    public final Map<String, double[][]> perAdapterEmbedDelta = new LinkedHashMap<>();
    public final Map<String, double[][]> perAdapterMlpDelta = new LinkedHashMap<>();

    public FusedState(int vocab, int embedDim) {
        this.vocab = vocab;
        this.embedDim = embedDim;
    }
}
