#!/bin/bash
# Oracle solve script for lora-adapter-attribution-merge.
#
# Overwrites the three pipeline components with implementations that:
#   1) express each adapter against the target snapshot correctly by
#      rescaling the effective MLP delta for the normalization-constant
#      drift in addition to resizing the embedding delta for the vocab
#      drift.
#   2) fuse aligned adapters by summing full effective deltas AND
#      materializing per-source shares so the state carries attribution.
#   3) exclude a named source by exact subtraction of its per-source
#      contribution rather than a mean-scale approximation.
# Then rebuilds the classes and runs the driver.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

# --- Component A: base-alignment (rebase) ---
cat > "${APP_ROOT}/src/main/java/io/terminus/stitch/align/AlignPolicy.java" <<'EOF'
package io.terminus.stitch.align;

import io.terminus.stitch.model.Adapter;
import io.terminus.stitch.model.AlignedAdapter;
import io.terminus.stitch.model.Snapshot;
import io.terminus.stitch.util.MatOps;

/**
 * Expresses an adapter's effective deltas against a chosen target snapshot.
 * Corrects for two independent axes of drift between snapshots:
 *   - the source's tokenizer vocabulary size vs. the target's, and
 *   - the target's residual-block normalization scale vs. the source's.
 * When the source and target are the same snapshot the returned deltas
 * equal the input's effective deltas.
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

        double numer = Math.sqrt(to.calMeanSq + to.rmsEps);
        double denom = Math.sqrt(from.calMeanSq + from.rmsEps);
        double scale = numer / denom;
        double[][] mOut = (scale == 1.0) ? eff_m : MatOps.scaled(eff_m, scale);

        return new AlignedAdapter(a.label, from.id, to.id, eOut, mOut);
    }
}
EOF

# --- Component B: state-fusion (merge) ---
cat > "${APP_ROOT}/src/main/java/io/terminus/stitch/blend/BlendKernel.java" <<'EOF'
package io.terminus.stitch.blend;

import io.terminus.stitch.model.AlignedAdapter;
import io.terminus.stitch.model.FusedState;
import io.terminus.stitch.model.Snapshot;
import io.terminus.stitch.util.MatOps;

import java.util.List;

/**
 * Fuses aligned adapters by summing their full effective deltas AND
 * materializing per-source shares. Downstream attribution consumers rely
 * on the per-source shares being the exact effective deltas that
 * accumulated into the merged state.
 */
public final class BlendKernel {

    public FusedState blend(List<AlignedAdapter> parts, Snapshot target) {
        FusedState st = new FusedState(target.vocabSize, target.embedDim);
        double[][] full_e = MatOps.zeros(target.vocabSize, target.embedDim);
        double[][] full_m = MatOps.zeros(target.embedDim, target.embedDim);

        for (AlignedAdapter p : parts) {
            MatOps.axpy(full_e, 1.0, p.effectiveEmbedDelta);
            MatOps.axpy(full_m, 1.0, p.effectiveMlpDelta);
            st.perAdapterEmbedDelta.put(p.label, MatOps.copy(p.effectiveEmbedDelta));
            st.perAdapterMlpDelta.put(p.label, MatOps.copy(p.effectiveMlpDelta));
        }

        st.fullEmbedDelta = full_e;
        st.fullMlpDelta = full_m;
        return st;
    }
}
EOF

# --- Component C: attribution-projection (decommission) ---
cat > "${APP_ROOT}/src/main/java/io/terminus/stitch/trace/TraceProjector.java" <<'EOF'
package io.terminus.stitch.trace;

import io.terminus.stitch.model.FusedState;
import io.terminus.stitch.util.MatOps;

/**
 * Produces a FusedState that represents the input with a named source's
 * contribution excluded by exact subtraction of its per-source deltas.
 * Sources not being excluded are carried through unchanged.
 */
public final class TraceProjector {

    public FusedState exclude(FusedState in, String id) {
        FusedState out = new FusedState(in.vocab, in.embedDim);
        out.fullEmbedDelta = MatOps.copy(in.fullEmbedDelta);
        out.fullMlpDelta = MatOps.copy(in.fullMlpDelta);

        double[][] pe = in.perAdapterEmbedDelta.get(id);
        double[][] pm = in.perAdapterMlpDelta.get(id);
        if (pe == null || pm == null) {
            throw new IllegalArgumentException(
                "cannot exclude '" + id + "': per-source share missing from fused state");
        }
        MatOps.axpy(out.fullEmbedDelta, -1.0, pe);
        MatOps.axpy(out.fullMlpDelta, -1.0, pm);

        for (var e : in.perAdapterEmbedDelta.entrySet()) {
            if (e.getKey().equals(id)) continue;
            out.perAdapterEmbedDelta.put(e.getKey(), MatOps.copy(e.getValue()));
        }
        for (var e : in.perAdapterMlpDelta.entrySet()) {
            if (e.getKey().equals(id)) continue;
            out.perAdapterMlpDelta.put(e.getKey(), MatOps.copy(e.getValue()));
        }
        return out;
    }
}
EOF

bash "${APP_ROOT}/scripts/run_merge.sh"
