package io.terminus.stitch.model;

/** Base snapshot metadata + tensors. */
public final class Snapshot {
    public final String id;
    public final int vocabSize;
    public final int embedDim;
    public final double[][] embedding;
    public final double[][] mlpWeight;
    public final double rmsEps;
    public final double calMeanSq;

    public Snapshot(String id, int vocabSize, int embedDim,
                    double[][] embedding, double[][] mlpWeight,
                    double rmsEps, double calMeanSq) {
        this.id = id;
        this.vocabSize = vocabSize;
        this.embedDim = embedDim;
        this.embedding = embedding;
        this.mlpWeight = mlpWeight;
        this.rmsEps = rmsEps;
        this.calMeanSq = calMeanSq;
    }
}
