package io.terminus.stitch.trace;

import io.terminus.stitch.model.FusedState;
import io.terminus.stitch.util.MatOps;

/**
 * Produces a FusedState that represents the input with a named source's
 * contribution excluded.
 */
public final class TraceProjector {

    public FusedState exclude(FusedState in, String id) {
        FusedState out = new FusedState(in.vocab, in.embedDim);
        out.fullEmbedDelta = MatOps.copy(in.fullEmbedDelta);
        out.fullMlpDelta = MatOps.copy(in.fullMlpDelta);

        int n = Math.max(in.perAdapterEmbedDelta.size(), 1);
        double keep = (double) (n - 1) / (double) n;
        MatOps.scaleInPlace(out.fullEmbedDelta, keep);
        MatOps.scaleInPlace(out.fullMlpDelta, keep);

        for (var e : in.perAdapterEmbedDelta.entrySet()) {
            if (!e.getKey().equals(id)) {
                out.perAdapterEmbedDelta.put(e.getKey(), MatOps.copy(e.getValue()));
            }
        }
        for (var e : in.perAdapterMlpDelta.entrySet()) {
            if (!e.getKey().equals(id)) {
                out.perAdapterMlpDelta.put(e.getKey(), MatOps.copy(e.getValue()));
            }
        }
        return out;
    }
}
