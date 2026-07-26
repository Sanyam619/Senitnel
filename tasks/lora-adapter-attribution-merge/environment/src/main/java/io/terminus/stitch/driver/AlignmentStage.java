package io.terminus.stitch.driver;

import io.terminus.stitch.align.AlignPolicy;
import io.terminus.stitch.model.Adapter;
import io.terminus.stitch.model.AlignedAdapter;
import io.terminus.stitch.model.Snapshot;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Stage that expresses every input adapter against the target snapshot. */
public final class AlignmentStage {
    private final AlignPolicy policy = new AlignPolicy();

    public List<AlignedAdapter> run(List<Adapter> adapters, Map<String, Snapshot> bases, String targetId) {
        Snapshot to = bases.get(targetId);
        if (to == null) throw new IllegalArgumentException("unknown target: " + targetId);
        List<AlignedAdapter> out = new ArrayList<>(adapters.size());
        for (Adapter a : adapters) {
            Snapshot from = bases.get(a.sourceSnapshot);
            if (from == null) throw new IllegalArgumentException("unknown source: " + a.sourceSnapshot);
            out.add(policy.align(a, from, to));
        }
        return out;
    }
}
