package io.terminus.stitch.io;

import io.terminus.stitch.model.Snapshot;
import io.terminus.stitch.util.MatOps;
import io.terminus.stitch.util.Prng;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Deterministic fixture generator invoked once at container build time.
 * Reads seeds.json and writes base snapshots, adapters, and eval tasks to
 * their target directories in a stable, cross-JDK reproducible way.
 */
public final class DataGenerator {

    public static void main(String[] args) throws Exception {
        Path seedsPath = null;
        Path basesDir = null;
        Path adaptersDir = null;
        Path evalDir = null;
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--seeds":    seedsPath   = Path.of(args[++i]); break;
                case "--bases":    basesDir    = Path.of(args[++i]); break;
                case "--adapters": adaptersDir = Path.of(args[++i]); break;
                case "--eval":     evalDir     = Path.of(args[++i]); break;
                default: throw new IllegalArgumentException("unknown arg: " + args[i]);
            }
        }
        if (seedsPath == null || basesDir == null || adaptersDir == null || evalDir == null) {
            throw new IllegalArgumentException("required: --seeds --bases --adapters --eval");
        }
        Map<String, Object> cfg = JsonReader.asObject(JsonReader.parse(Files.readString(seedsPath)));

        int embedDim = JsonReader.asInt(cfg.get("embed_dim"));
        int vocabS1 = JsonReader.asInt(cfg.get("vocab_S1"));
        int vocabS2 = JsonReader.asInt(cfg.get("vocab_S2"));
        int vocabS3 = JsonReader.asInt(cfg.get("vocab_S3"));
        double eps1 = JsonReader.asDouble(cfg.get("rms_eps_S1"));
        double eps2 = JsonReader.asDouble(cfg.get("rms_eps_S2"));
        double eps3 = JsonReader.asDouble(cfg.get("rms_eps_S3"));
        double cal1 = JsonReader.asDouble(cfg.get("cal_mean_sq_S1"));
        double cal2 = JsonReader.asDouble(cfg.get("cal_mean_sq_S2"));
        double cal3 = JsonReader.asDouble(cfg.get("cal_mean_sq_S3"));
        int rank = JsonReader.asInt(cfg.get("adapter_rank"));

        Map<String, Object> baseSeeds = JsonReader.asObject(cfg.get("base_seeds"));
        long s1EmbedSeed = JsonReader.asLong(baseSeeds.get("S1_embed"));
        long s1MlpSeed = JsonReader.asLong(baseSeeds.get("S1_mlp"));
        long s2ExtraEmbedSeed = JsonReader.asLong(baseSeeds.get("S2_embed_extra"));
        long s2MlpSeed = JsonReader.asLong(baseSeeds.get("S2_mlp"));
        long s3MlpSeed = JsonReader.asLong(baseSeeds.get("S3_mlp"));

        // Base embeddings: S1 has vocabS1 rows. S2 extends with (vocabS2 - vocabS1) new rows.
        // S3 has the same vocab and embedding as S2 (only rms_eps changed).
        double[][] embS1 = gaussianMatrix(new Prng(s1EmbedSeed), vocabS1, embedDim, 0.5);
        double[][] embExtra = gaussianMatrix(new Prng(s2ExtraEmbedSeed), vocabS2 - vocabS1, embedDim, 0.5);
        double[][] embS2 = concatRows(embS1, embExtra);
        double[][] embS3 = MatOps.copy(embS2);

        double[][] mlpS1 = gaussianMatrix(new Prng(s1MlpSeed), embedDim, embedDim, 0.3);
        double[][] mlpS2 = MatOps.copy(mlpS1); // seed = s2MlpSeed same as s1MlpSeed by config
        double[][] mlpS3 = MatOps.copy(mlpS1); // same weight, only rms_eps drifts S2 -> S3
        if (s2MlpSeed != s1MlpSeed) {
            mlpS2 = gaussianMatrix(new Prng(s2MlpSeed), embedDim, embedDim, 0.3);
        }
        if (s3MlpSeed != s1MlpSeed) {
            mlpS3 = gaussianMatrix(new Prng(s3MlpSeed), embedDim, embedDim, 0.3);
        }

        writeSnapshot(basesDir.resolve("S1.json"), "S1", vocabS1, embedDim, embS1, mlpS1, eps1, cal1);
        writeSnapshot(basesDir.resolve("S2.json"), "S2", vocabS2, embedDim, embS2, mlpS2, eps2, cal2);
        writeSnapshot(basesDir.resolve("S3.json"), "S3", vocabS3, embedDim, embS3, mlpS3, eps3, cal3);

        // Adapters.
        List<Object> adapters = JsonReader.asArray(cfg.get("adapters"));
        for (Object ao : adapters) {
            Map<String, Object> a = JsonReader.asObject(ao);
            String label = JsonReader.asString(a.get("label"));
            String src = JsonReader.asString(a.get("source_snapshot"));
            long seed = JsonReader.asLong(a.get("seed"));
            int srcVocab = switch (src) {
                case "S1" -> vocabS1;
                case "S2" -> vocabS2;
                case "S3" -> vocabS3;
                default -> throw new IllegalArgumentException("bad source_snapshot: " + src);
            };
            Prng rng = new Prng(seed);
            double[][] eA = gaussianMatrix(rng, rank, embedDim, 0.1);
            double[][] eB = gaussianMatrix(rng, srcVocab, rank, 0.1);
            double[][] mA = gaussianMatrix(rng, rank, embedDim, 0.1);
            double[][] mB = gaussianMatrix(rng, embedDim, rank, 0.1);
            writeAdapter(adaptersDir.resolve(label + ".json"), label, src, rank, eA, eB, mA, mB);
        }

        // Eval outputs are computed from a forward pass on S3 with a
        // reference delta whose direction the adapters partially align
        // with. The reference delta is built inline (independent of
        // AlignPolicy) using the analytically correct rebase rules so the
        // fixtures never depend on the agent's implementation.
        Snapshot s1 = new Snapshot("S1", vocabS1, embedDim, embS1, mlpS1, eps1, cal1);
        Snapshot s2 = new Snapshot("S2", vocabS2, embedDim, embS2, mlpS2, eps2, cal2);
        Snapshot s3 = new Snapshot("S3", vocabS3, embedDim, embS3, mlpS3, eps3, cal3);
        Snapshot[] sources = new Snapshot[adapters.size()];
        double[][] refEmbed = MatOps.zeros(vocabS3, embedDim);
        double[][] refMlp = MatOps.zeros(embedDim, embedDim);
        for (int ai = 0; ai < adapters.size(); ai++) {
            Map<String, Object> a = JsonReader.asObject(adapters.get(ai));
            String src = JsonReader.asString(a.get("source_snapshot"));
            long seed = JsonReader.asLong(a.get("seed"));
            int srcVocab = switch (src) {
                case "S1" -> vocabS1;
                case "S2" -> vocabS2;
                case "S3" -> vocabS3;
                default -> throw new IllegalArgumentException("bad source_snapshot: " + src);
            };
            Snapshot from = switch (src) {
                case "S1" -> s1;
                case "S2" -> s2;
                case "S3" -> s3;
                default -> throw new IllegalArgumentException("bad source_snapshot: " + src);
            };
            sources[ai] = from;
            Prng rng = new Prng(seed);
            double[][] eA = gaussianMatrix(rng, rank, embedDim, 0.1);
            double[][] eB = gaussianMatrix(rng, srcVocab, rank, 0.1);
            double[][] mA = gaussianMatrix(rng, rank, embedDim, 0.1);
            double[][] mB = gaussianMatrix(rng, embedDim, rank, 0.1);
            double[][] effE = MatOps.mul(eB, eA);
            double[][] effM = MatOps.mul(mB, mA);
            double[][] rebasedE = MatOps.resizeRows(effE, vocabS3);
            // Fixture-only port of the dense MLP delta onto S3. Kept as a
            // local helper so the ratio is not an obvious one-liner agents
            // can paste into AlignPolicy.
            double[][] rebasedM = portDenseMlp(effM, from, s3);
            MatOps.axpy(refEmbed, 1.0, rebasedE);
            MatOps.axpy(refMlp, 1.0, rebasedM);
        }
        // Reference direction is twice the merged delta so the correctly-
        // merged pipeline only closes half the gap; this keeps every score
        // strictly negative but leaves the merged run substantially closer
        // to the target than the baseline.
        double[][] targetEmbed = MatOps.scaled(refEmbed, 2.0);
        double[][] targetMlp = MatOps.scaled(refMlp, 2.0);

        List<Object> evals = JsonReader.asArray(cfg.get("eval"));
        for (Object eo : evals) {
            Map<String, Object> e = JsonReader.asObject(eo);
            String taskId = JsonReader.asString(e.get("task_id"));
            long seed = JsonReader.asLong(e.get("seed"));
            int n = JsonReader.asInt(e.get("n_examples"));
            int k = JsonReader.asInt(e.get("tokens_per_example"));
            Prng rng = new Prng(seed);
            int[][] inputs = new int[n][k];
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < k; j++) {
                    inputs[i][j] = Math.floorMod(rng.nextLong(), vocabS3);
                }
            }
            double[][] expected = new double[n][embedDim];
            for (int i = 0; i < n; i++) {
                double[] y = io.terminus.stitch.forward.Forward.apply(s3, targetEmbed, targetMlp, inputs[i]);
                for (int d = 0; d < embedDim; d++) expected[i][d] = y[d];
            }
            writeEvalTask(evalDir.resolve(taskId + ".json"), taskId, inputs, expected);
        }
    }

    private static double[][] portDenseMlp(double[][] effM, Snapshot from, Snapshot to) {
        double src = from.calMeanSq + from.rmsEps;
        double tgt = to.calMeanSq + to.rmsEps;
        if (!(src > 0.0) || !(tgt > 0.0)) {
            throw new IllegalStateException("non-positive calibration gate");
        }
        return MatOps.scaled(effM, Math.sqrt(tgt / src));
    }

    private static double[][] gaussianMatrix(Prng rng, int rows, int cols, double scale) {
        double[][] m = new double[rows][cols];
        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < cols; j++) {
                m[i][j] = rng.nextGaussian() * scale;
            }
        }
        return m;
    }

    private static double[][] concatRows(double[][] a, double[][] b) {
        int cols = a[0].length;
        double[][] out = new double[a.length + b.length][cols];
        for (int i = 0; i < a.length; i++) System.arraycopy(a[i], 0, out[i], 0, cols);
        for (int i = 0; i < b.length; i++) System.arraycopy(b[i], 0, out[a.length + i], 0, cols);
        return out;
    }

    private static void writeSnapshot(Path p, String id, int vocab, int embed,
                                      double[][] embMat, double[][] mlp,
                                      double eps, double cal) throws IOException {
        LinkedHashMap<String, Object> o = new LinkedHashMap<>();
        o.put("id", id);
        o.put("vocab_size", (long) vocab);
        o.put("embed_dim", (long) embed);
        o.put("embedding", embMat);
        o.put("mlp_weight", mlp);
        o.put("rms_eps", eps);
        o.put("cal_mean_sq", cal);
        writeJson(p, o);
    }

    private static void writeAdapter(Path p, String label, String src, int rank,
                                     double[][] eA, double[][] eB,
                                     double[][] mA, double[][] mB) throws IOException {
        LinkedHashMap<String, Object> o = new LinkedHashMap<>();
        o.put("label", label);
        o.put("source_snapshot", src);
        o.put("rank", (long) rank);
        o.put("embed_A", eA);
        o.put("embed_B", eB);
        o.put("mlp_A", mA);
        o.put("mlp_B", mB);
        writeJson(p, o);
    }

    private static void writeEvalTask(Path p, String taskId, int[][] inputs, double[][] expected) throws IOException {
        LinkedHashMap<String, Object> o = new LinkedHashMap<>();
        o.put("task_id", taskId);
        List<Object> rows = new ArrayList<>();
        for (int[] row : inputs) rows.add(row);
        o.put("inputs", rows);
        o.put("expected", expected);
        writeJson(p, o);
    }

    private static void writeJson(Path p, Object v) throws IOException {
        JsonWriter w = new JsonWriter();
        w.writeAny(v);
        Files.createDirectories(p.getParent());
        Files.writeString(p, w.toString());
    }
}
