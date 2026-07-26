package io.terminus.stitch.driver;

import io.terminus.stitch.blend.BlendKernel;
import io.terminus.stitch.model.AlignedAdapter;
import io.terminus.stitch.model.FusedState;
import io.terminus.stitch.model.Snapshot;

import java.util.List;

/** Stage that fuses aligned adapters into a single merged state. */
public final class FusionStage {
    private final BlendKernel kernel = new BlendKernel();

    public FusedState run(List<AlignedAdapter> aligned, Snapshot target) {
        return kernel.blend(aligned, target);
    }
}
