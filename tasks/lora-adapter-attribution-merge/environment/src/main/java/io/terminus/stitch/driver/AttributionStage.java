package io.terminus.stitch.driver;

import io.terminus.stitch.model.FusedState;
import io.terminus.stitch.trace.TraceProjector;

/** Stage that produces per-source excluded variants of a merged state. */
public final class AttributionStage {
    private final TraceProjector projector = new TraceProjector();

    public FusedState without(FusedState fused, String label) {
        return projector.exclude(fused, label);
    }
}
