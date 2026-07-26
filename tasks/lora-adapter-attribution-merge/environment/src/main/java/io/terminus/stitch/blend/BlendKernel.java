package io.terminus.stitch.blend;

import io.terminus.stitch.model.AlignedAdapter;
import io.terminus.stitch.model.FusedState;
import io.terminus.stitch.model.Snapshot;
import io.terminus.stitch.util.MatOps;

import java.util.List;

/**
 * Fuses aligned adapters into a single FusedState against a target snapshot.
 */
public final class BlendKernel {

    public FusedState blend(List<AlignedAdapter> parts, Snapshot target) {
        FusedState st = new FusedState(target.vocabSize, target.embedDim);

        double[][] full_e = MatOps.zeros(target.vocabSize, target.embedDim);
        double[][] full_m = MatOps.zeros(target.embedDim, target.embedDim);
        double share = parts.isEmpty() ? 1.0 : (1.0 / (double) parts.size());

        for (AlignedAdapter p : parts) {
            MatOps.axpy(full_e, 1.0, p.effectiveEmbedDelta);
            MatOps.axpy(full_m, 1.0, p.effectiveMlpDelta);
            st.perAdapterEmbedDelta.put(p.label, MatOps.scaled(p.effectiveEmbedDelta, share));
            st.perAdapterMlpDelta.put(p.label, MatOps.scaled(p.effectiveMlpDelta, share));
        }

        st.fullEmbedDelta = full_e;
        st.fullMlpDelta = full_m;
        return st;
    }
}
