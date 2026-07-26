package io.terminus.stitch.align;

import io.terminus.stitch.model.Adapter;
import io.terminus.stitch.model.AlignedAdapter;
import io.terminus.stitch.model.Snapshot;
import io.terminus.stitch.util.MatOps;

/**
 * Expresses an adapter's effective deltas against a chosen target snapshot.
 *
 * The returned AlignedAdapter carries dense effective embedding and MLP
 * deltas (not the factored A/B pair).
 */
public final class AlignPolicy {

    public AlignedAdapter align(Adapter a, Snapshot from, Snapshot to) {
        double[][] eff_e = MatOps.mul(a.embedB, a.embedA);
        double[][] eff_m = MatOps.mul(a.mlpB, a.mlpA);

        double[][] eOut;
        if (from.vocabSize == to.vocabSize) {
            eOut = eff_e;
        } else {
            eOut = MatOps.resizeRows(eff_e, to.vocabSize);
        }

        double scale = Math.sqrt(from.rmsEps / to.rmsEps);
        double[][] mOut = (scale == 1.0) ? eff_m : MatOps.scaled(eff_m, scale);

        return new AlignedAdapter(a.label, from.id, to.id, eOut, mOut);
    }
}
