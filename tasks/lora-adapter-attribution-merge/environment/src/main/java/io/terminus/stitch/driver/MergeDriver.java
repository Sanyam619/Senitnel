package io.terminus.stitch.driver;

import io.terminus.stitch.forward.Forward;
import io.terminus.stitch.io.Datasets;
import io.terminus.stitch.io.JsonWriter;
import io.terminus.stitch.model.Adapter;
import io.terminus.stitch.model.AlignedAdapter;
import io.terminus.stitch.model.EvalTask;
import io.terminus.stitch.model.FusedState;
import io.terminus.stitch.model.Snapshot;
import io.terminus.stitch.util.MatOps;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * End-to-end merge pipeline driver. Loads inputs, drives the three
 * pipeline stages, evaluates on every downstream task, and writes the
 * result report as JSON.
 */
public final class MergeDriver {

    public static void main(String[] args) throws Exception {
        Path basesDir = null;
        Path adaptersDir = null;
        Path evalDir = null;
        Path reportPath = null;
        String target = "S3";
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--bases":    basesDir    = Path.of(args[++i]); break;
                case "--adapters": adaptersDir = Path.of(args[++i]); break;
                case "--eval":     evalDir     = Path.of(args[++i]); break;
                case "--report":   reportPath  = Path.of(args[++i]); break;
                case "--target":   target      = args[++i]; break;
                default: throw new IllegalArgumentException("unknown arg: " + args[i]);
            }
        }
        if (basesDir == null || adaptersDir == null || evalDir == null || reportPath == null) {
            throw new IllegalArgumentException("required: --bases --adapters --eval --report");
        }

        Map<String, Snapshot> bases = Datasets.loadAllSnapshots(basesDir);
        List<Adapter> adapters = Datasets.loadAllAdapters(adaptersDir);
        List<EvalTask> tasks = Datasets.loadAllEvalTasks(evalDir);

        Snapshot targetBase = bases.get(target);
        if (targetBase == null) throw new IllegalArgumentException("unknown target: " + target);

        List<AlignedAdapter> aligned = new AlignmentStage().run(adapters, bases, target);
        FusedState fused = new FusionStage().run(aligned, targetBase);
        AttributionStage attribution = new AttributionStage();

        // --- adapters section ---
        List<Object> adaptersOut = new ArrayList<>();
        for (int i = 0; i < adapters.size(); i++) {
            Adapter a = adapters.get(i);
            AlignedAdapter al = aligned.get(i);
            double rebasedNorm = Math.sqrt(
                    MatOps.frobeniusSquared(al.effectiveEmbedDelta) +
                    MatOps.frobeniusSquared(al.effectiveMlpDelta));
            double contribNorm = 0.0;
            double[][] pe = fused.perAdapterEmbedDelta.get(a.label);
            double[][] pm = fused.perAdapterMlpDelta.get(a.label);
            if (pe != null) contribNorm += MatOps.frobeniusSquared(pe);
            if (pm != null) contribNorm += MatOps.frobeniusSquared(pm);
            contribNorm = Math.sqrt(contribNorm);

            LinkedHashMap<String, Object> row = new LinkedHashMap<>();
            row.put("label", a.label);
            row.put("source_snapshot", a.sourceSnapshot);
            row.put("target_snapshot", target);
            row.put("rebased_norm", rebasedNorm);
            row.put("contribution_norm", contribNorm);
            adaptersOut.add(row);
        }

        // --- evaluation section ---
        List<Object> evalOut = new ArrayList<>();
        for (EvalTask t : tasks) {
            double baseline = Forward.score(targetBase, null, null, t);
            double merged = Forward.score(targetBase, fused.fullEmbedDelta, fused.fullMlpDelta, t);
            LinkedHashMap<String, Object> decommission = new LinkedHashMap<>();
            for (Adapter a : adapters) {
                FusedState without = attribution.without(fused, a.label);
                double sc = Forward.score(targetBase, without.fullEmbedDelta, without.fullMlpDelta, t);
                decommission.put(a.label, sc);
            }
            LinkedHashMap<String, Object> row = new LinkedHashMap<>();
            row.put("task_id", t.taskId);
            row.put("baseline_score", baseline);
            row.put("merged_score", merged);
            row.put("decommission_scores", decommission);
            evalOut.add(row);
        }

        // --- attribution section ---
        double total = Math.sqrt(
                MatOps.frobeniusSquared(fused.fullEmbedDelta) +
                MatOps.frobeniusSquared(fused.fullMlpDelta));
        double sumSquared = 0.0;
        for (String k : fused.perAdapterEmbedDelta.keySet()) {
            sumSquared += MatOps.frobeniusSquared(fused.perAdapterEmbedDelta.get(k));
            double[][] pm = fused.perAdapterMlpDelta.get(k);
            if (pm != null) sumSquared += MatOps.frobeniusSquared(pm);
        }
        double[][] residE = MatOps.copy(fused.fullEmbedDelta);
        double[][] residM = MatOps.copy(fused.fullMlpDelta);
        for (String k : fused.perAdapterEmbedDelta.keySet()) {
            MatOps.axpy(residE, -1.0, fused.perAdapterEmbedDelta.get(k));
            double[][] pm = fused.perAdapterMlpDelta.get(k);
            if (pm != null) MatOps.axpy(residM, -1.0, pm);
        }
        double residualNorm = Math.sqrt(
                MatOps.frobeniusSquared(residE) +
                MatOps.frobeniusSquared(residM));

        LinkedHashMap<String, Object> attrOut = new LinkedHashMap<>();
        attrOut.put("total_delta_frobenius", total);
        attrOut.put("sum_per_adapter_frobenius_squared", sumSquared);
        attrOut.put("residual_after_all_decommission", residualNorm);

        // --- final report ---
        LinkedHashMap<String, Object> report = new LinkedHashMap<>();
        report.put("schema_tag", "lora-merge-v1");
        report.put("adapters", adaptersOut);
        report.put("evaluation", evalOut);
        report.put("attribution", attrOut);

        JsonWriter w = new JsonWriter();
        w.writeAny(report);
        Files.createDirectories(reportPath.getParent());
        Files.writeString(reportPath, w.toString());
    }
}
