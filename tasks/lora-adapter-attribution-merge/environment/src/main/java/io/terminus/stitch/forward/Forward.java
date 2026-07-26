package io.terminus.stitch.forward;

import io.terminus.stitch.model.EvalTask;
import io.terminus.stitch.model.Snapshot;

/** Forward pass over a single base + an optional applied delta. */
public final class Forward {
    private Forward() {}

    /**
     * Single-example forward pass.
     * @param base       base snapshot
     * @param embedDelta additive embedding delta (target_vocab x embed_dim), or null for zero
     * @param mlpDelta   additive MLP delta (embed_dim x embed_dim), or null for zero
     * @param tokens     input token ids
     * @return           output vector of length embed_dim
     */
    public static double[] apply(Snapshot base, double[][] embedDelta, double[][] mlpDelta, int[] tokens) {
        int d = base.embedDim;
        double[] y = new double[d];
        for (int t : tokens) {
            double[] row = base.embedding[t];
            for (int i = 0; i < d; i++) y[i] += row[i];
            if (embedDelta != null) {
                double[] drow = embedDelta[t];
                for (int i = 0; i < d; i++) y[i] += drow[i];
            }
        }
        double ss = 0.0;
        for (int i = 0; i < d; i++) ss += y[i] * y[i];
        double meanSq = ss / d;
        double scale = 1.0 / Math.sqrt(meanSq + base.rmsEps);
        double[] h = new double[d];
        for (int i = 0; i < d; i++) h[i] = y[i] * scale;
        double[] z = new double[d];
        for (int i = 0; i < d; i++) {
            double acc = 0.0;
            double[] wrow = base.mlpWeight[i];
            for (int j = 0; j < d; j++) acc += wrow[j] * h[j];
            if (mlpDelta != null) {
                double[] drow = mlpDelta[i];
                for (int j = 0; j < d; j++) acc += drow[j] * h[j];
            }
            z[i] = acc;
        }
        return z;
    }

    /** Score = -mean_squared_error over the entire eval task. */
    public static double score(Snapshot base, double[][] embedDelta, double[][] mlpDelta, EvalTask task) {
        int d = base.embedDim;
        int n = task.inputs.length;
        double totalSq = 0.0;
        int count = 0;
        for (int i = 0; i < n; i++) {
            double[] out = apply(base, embedDelta, mlpDelta, task.inputs[i]);
            double[] exp = task.expected[i];
            for (int j = 0; j < d; j++) {
                double diff = out[j] - exp[j];
                totalSq += diff * diff;
                count++;
            }
        }
        return -(totalSq / count);
    }
}
