package io.terminus.stitch.verify;

import io.terminus.stitch.align.AlignPolicy;
import io.terminus.stitch.blend.BlendKernel;
import io.terminus.stitch.forward.Forward;
import io.terminus.stitch.io.Datasets;
import io.terminus.stitch.model.Adapter;
import io.terminus.stitch.model.AlignedAdapter;
import io.terminus.stitch.model.EvalTask;
import io.terminus.stitch.model.FusedState;
import io.terminus.stitch.model.Snapshot;
import io.terminus.stitch.trace.TraceProjector;
import io.terminus.stitch.util.MatOps;
import io.terminus.stitch.util.Prng;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Verifier-owned behavioral probe. Imports the current pipeline packages
 * and drives them with verifier-controlled inputs so that a hand-written
 * merge-report.json cannot mask defects the underlying components must
 * fix. Exits non-zero on any check failure with a descriptive stderr line.
 */
public final class Verify {

    private static final double TOL = 1.0e-9;

    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            fail("usage: Verify <subcommand>");
        }
        String cmd = args[0];
        switch (cmd) {
            case "align_scale":                        runAlignScale();               break;
            case "align_identity":                     runAlignIdentity();            break;
            case "align_vocab":                        runAlignVocab();               break;
            case "fuse_shares":                        runFuseShares();               break;
            case "roundtrip":                          runExcludeRoundtrip();         break;
            case "reblend_eq":                         runExcludeEqualsReblend();     break;
            case "gamma_recovers":                     runGammaRecovers();            break;
            default: fail("unknown subcommand: " + cmd);
        }
    }

    /**
     * On shared tokens, the marginal residual-block contribution of an
     * adapter (forward-with-delta minus forward-without-delta) must match
     * after rebase when the two snapshots share embeddings/weights and the
     * probe activation energy equals each snapshot's recorded calibration
     * energy. This is the observable the rebase is supposed to preserve;
     * it does not prescribe a closed-form scale factor.
     */
    private static void runAlignScale() {
        int d = 4;
        double cal = 1.0;
        Snapshot s2 = mkCalibratedSnapshot("S2", 6, d, cal, 1.0e-4);
        Snapshot s3 = mkCalibratedSnapshot("S3", 6, d, cal, 1.0e-6);
        Adapter a = mkAdapter("probe", "S2", 2, 6, d, 200L);
        AlignedAdapter out = new AlignPolicy().align(a, s2, s3);
        double[][] srcMlp = MatOps.mul(a.mlpB, a.mlpA);
        int[] tokens = new int[] {0};
        // Hold the embedding path at zero so the residual-block energy stays
        // on the calibrated meanSq; this isolates the MLP rebase observable.
        double[] marginSrc = marginal(s2, null, srcMlp, tokens);
        double[] marginTgt = marginal(s3, null, out.effectiveMlpDelta, tokens);
        double worst = 0.0;
        for (int i = 0; i < d; i++) {
            worst = Math.max(worst, Math.abs(marginSrc[i] - marginTgt[i]));
        }
        if (worst > 1.0e-8) {
            fail("align_scale.marginal: max abs diff " + worst
                    + " (rebase does not preserve residual-block contribution)");
        }
    }

    private static double[] marginal(Snapshot base, double[][] eDelta, double[][] mDelta, int[] tokens) {
        double[] with = Forward.apply(base, eDelta, mDelta, tokens);
        double[] without = Forward.apply(base, null, null, tokens);
        double[] out = new double[with.length];
        for (int i = 0; i < with.length; i++) out[i] = with[i] - without[i];
        return out;
    }

    /** Snapshot whose row-0 embedding is constant so a single-token probe has meanSq == cal. */
    private static Snapshot mkCalibratedSnapshot(String id, int v, int d, double cal, double eps) {
        double[][] emb = new double[v][d];
        double cell = Math.sqrt(cal);
        for (int i = 0; i < v; i++) {
            for (int j = 0; j < d; j++) emb[i][j] = cell;
        }
        double[][] mlp = new double[d][d];
        for (int i = 0; i < d; i++) {
            for (int j = 0; j < d; j++) mlp[i][j] = (i == j) ? 0.4 : 0.05;
        }
        return new Snapshot(id, v, d, emb, mlp, eps, cal);
    }

    private static void runAlignIdentity() {
        int d = 4;
        Snapshot s3 = mkSnapshot("S3", 6, d, 0.85, 1.0e-6, 300L);
        Adapter a = mkAdapter("probe", "S3", 2, 6, d, 400L);
        AlignedAdapter out = new AlignPolicy().align(a, s3, s3);
        double[][] expE = MatOps.mul(a.embedB, a.embedA);
        double[][] expM = MatOps.mul(a.mlpB, a.mlpA);
        checkClose("align_identity.embed", expE, out.effectiveEmbedDelta, TOL);
        checkClose("align_identity.mlp",   expM, out.effectiveMlpDelta,   TOL);
    }

    private static void runAlignVocab() {
        int d = 3;
        Snapshot s1 = mkSnapshot("S1", 4, d, 0.90, 1.0e-4, 500L);
        Snapshot s3 = mkSnapshot("S3", 7, d, 0.90, 1.0e-6, 500L);
        Adapter a = mkAdapter("probe", "S1", 2, 4, d, 600L);
        AlignedAdapter out = new AlignPolicy().align(a, s1, s3);
        if (out.effectiveEmbedDelta.length != s3.vocabSize) {
            fail("align_vocab: expected embed delta with " + s3.vocabSize
                    + " rows, got " + out.effectiveEmbedDelta.length);
        }
        double[][] baselineE = MatOps.mul(a.embedB, a.embedA);
        for (int i = 0; i < s1.vocabSize; i++) {
            for (int j = 0; j < d; j++) {
                if (Math.abs(out.effectiveEmbedDelta[i][j] - baselineE[i][j]) > TOL) {
                    fail("align_vocab: shared-token row " + i + " col " + j + " drifted");
                }
            }
        }
        for (int i = s1.vocabSize; i < s3.vocabSize; i++) {
            for (int j = 0; j < d; j++) {
                if (out.effectiveEmbedDelta[i][j] != 0.0) {
                    fail("align_vocab: new-token row " + i + " col " + j + " should be zero");
                }
            }
        }
    }

    private static void runFuseShares() {
        int d = 3, v = 5;
        Snapshot s3 = mkSnapshot("S3", v, d, 0.90, 1.0e-6, 700L);
        List<AlignedAdapter> parts = new ArrayList<>();
        AlignedAdapter x = mkAligned("x", v, d, 800L);
        AlignedAdapter y = mkAligned("y", v, d, 900L);
        AlignedAdapter z = mkAligned("z", v, d, 1000L);
        parts.add(x); parts.add(y); parts.add(z);
        FusedState fs = new BlendKernel().blend(parts, s3);
        if (fs.perAdapterEmbedDelta.size() != 3 || fs.perAdapterMlpDelta.size() != 3) {
            fail("fuse_shares: expected 3 per-source shares, got embed="
                    + fs.perAdapterEmbedDelta.size() + " mlp=" + fs.perAdapterMlpDelta.size());
        }
        checkClose("fuse_shares.x.embed", x.effectiveEmbedDelta, fs.perAdapterEmbedDelta.get("x"), TOL);
        checkClose("fuse_shares.y.mlp",   y.effectiveMlpDelta,   fs.perAdapterMlpDelta.get("y"),   TOL);
        double[][] sumE = MatOps.zeros(v, d);
        double[][] sumM = MatOps.zeros(d, d);
        for (AlignedAdapter a : parts) {
            MatOps.axpy(sumE, 1.0, a.effectiveEmbedDelta);
            MatOps.axpy(sumM, 1.0, a.effectiveMlpDelta);
        }
        checkClose("fuse_shares.full_embed", sumE, fs.fullEmbedDelta, TOL);
        checkClose("fuse_shares.full_mlp",   sumM, fs.fullMlpDelta,   TOL);
    }

    private static void runExcludeRoundtrip() {
        int d = 3, v = 5;
        Snapshot s3 = mkSnapshot("S3", v, d, 0.90, 1.0e-6, 1100L);
        List<AlignedAdapter> parts = new ArrayList<>();
        parts.add(mkAligned("x", v, d, 1200L));
        parts.add(mkAligned("y", v, d, 1300L));
        parts.add(mkAligned("z", v, d, 1400L));
        FusedState fs = new BlendKernel().blend(parts, s3);
        double[][] origE = MatOps.copy(fs.fullEmbedDelta);
        double[][] origM = MatOps.copy(fs.fullMlpDelta);
        double[][] yShareE = MatOps.copy(fs.perAdapterEmbedDelta.get("y"));
        double[][] yShareM = MatOps.copy(fs.perAdapterMlpDelta.get("y"));
        FusedState wo = new TraceProjector().exclude(fs, "y");
        double[][] restoredE = MatOps.copy(wo.fullEmbedDelta);
        double[][] restoredM = MatOps.copy(wo.fullMlpDelta);
        MatOps.axpy(restoredE, 1.0, yShareE);
        MatOps.axpy(restoredM, 1.0, yShareM);
        checkClose("exclude_roundtrip.embed", origE, restoredE, TOL);
        checkClose("exclude_roundtrip.mlp",   origM, restoredM, TOL);
    }

    private static void runExcludeEqualsReblend() {
        int d = 4, v = 6;
        Snapshot s3 = mkSnapshot("S3", v, d, 0.85, 1.0e-6, 1500L);
        List<AlignedAdapter> all = new ArrayList<>();
        List<AlignedAdapter> withoutG = new ArrayList<>();
        AlignedAdapter a1 = mkAligned("a1", v, d, 1600L);
        AlignedAdapter a2 = mkAligned("a2", v, d, 1700L);
        AlignedAdapter g  = mkAligned("g",  v, d, 1800L);
        AlignedAdapter a4 = mkAligned("a4", v, d, 1900L);
        all.add(a1); all.add(a2); all.add(g); all.add(a4);
        withoutG.add(a1); withoutG.add(a2); withoutG.add(a4);
        FusedState fs = new BlendKernel().blend(all, s3);
        FusedState viaExclude = new TraceProjector().exclude(fs, "g");
        FusedState viaReblend = new BlendKernel().blend(withoutG, s3);
        checkClose("exclude_equals_reblend.embed",
                viaReblend.fullEmbedDelta, viaExclude.fullEmbedDelta, TOL);
        checkClose("exclude_equals_reblend.mlp",
                viaReblend.fullMlpDelta, viaExclude.fullMlpDelta, TOL);
        EvalTask task = mkEvalTask("probe", 8, 3, v, d, 2000L, 2100L);
        double sExclude = Forward.score(s3, viaExclude.fullEmbedDelta, viaExclude.fullMlpDelta, task);
        double sReblend = Forward.score(s3, viaReblend.fullEmbedDelta, viaReblend.fullMlpDelta, task);
        if (Math.abs(sExclude - sReblend) > 1.0e-8) {
            fail("exclude_equals_reblend.score: exclude=" + sExclude + " reblend=" + sReblend);
        }
    }

    private static void runGammaRecovers() throws Exception {
        Path basesDir = Path.of("/app/data/bases");
        Path adaptersDir = Path.of("/app/data/adapters");
        Path evalDir = Path.of("/app/data/eval");
        Map<String, Snapshot> bases = Datasets.loadAllSnapshots(basesDir);
        List<Adapter> adapters = Datasets.loadAllAdapters(adaptersDir);
        List<EvalTask> tasks = Datasets.loadAllEvalTasks(evalDir);
        Snapshot target = bases.get("S3");

        AlignPolicy align = new AlignPolicy();
        BlendKernel blend = new BlendKernel();
        TraceProjector proj = new TraceProjector();

        List<AlignedAdapter> aligned = new ArrayList<>();
        List<AlignedAdapter> withoutGammaAligned = new ArrayList<>();
        for (Adapter a : adapters) {
            AlignedAdapter al = align.align(a, bases.get(a.sourceSnapshot), target);
            aligned.add(al);
            if (!a.label.equals("gamma")) withoutGammaAligned.add(al);
        }
        FusedState full = blend.blend(aligned, target);
        FusedState reblended = blend.blend(withoutGammaAligned, target);
        FusedState excluded = proj.exclude(full, "gamma");

        for (EvalTask t : tasks) {
            double sExcluded = Forward.score(target, excluded.fullEmbedDelta, excluded.fullMlpDelta, t);
            double sReblended = Forward.score(target, reblended.fullEmbedDelta, reblended.fullMlpDelta, t);
            if (Math.abs(sExcluded - sReblended) > 1.0e-8) {
                fail("gamma_recovers.real[" + t.taskId + "]: excluded=" + sExcluded
                        + " reblended=" + sReblended
                        + " diff=" + Math.abs(sExcluded - sReblended));
            }
        }
    }

    private static Snapshot mkSnapshot(String id, int v, int d, double cal, double eps, long seed) {
        Prng r = new Prng(seed);
        double[][] emb = new double[v][d];
        double[][] mlp = new double[d][d];
        for (int i = 0; i < v; i++) for (int j = 0; j < d; j++) emb[i][j] = r.nextGaussian() * 0.5;
        for (int i = 0; i < d; i++) for (int j = 0; j < d; j++) mlp[i][j] = r.nextGaussian() * 0.3;
        return new Snapshot(id, v, d, emb, mlp, eps, cal);
    }

    private static Adapter mkAdapter(String label, String src, int rank, int vocab, int d, long seed) {
        Prng r = new Prng(seed);
        double[][] eA = new double[rank][d];
        double[][] eB = new double[vocab][rank];
        double[][] mA = new double[rank][d];
        double[][] mB = new double[d][rank];
        for (int i = 0; i < rank; i++) for (int j = 0; j < d; j++) eA[i][j] = r.nextGaussian() * 0.1;
        for (int i = 0; i < vocab; i++) for (int j = 0; j < rank; j++) eB[i][j] = r.nextGaussian() * 0.1;
        for (int i = 0; i < rank; i++) for (int j = 0; j < d; j++) mA[i][j] = r.nextGaussian() * 0.1;
        for (int i = 0; i < d; i++) for (int j = 0; j < rank; j++) mB[i][j] = r.nextGaussian() * 0.1;
        return new Adapter(label, src, rank, eA, eB, mA, mB);
    }

    private static AlignedAdapter mkAligned(String label, int v, int d, long seed) {
        Prng r = new Prng(seed);
        double[][] e = new double[v][d];
        double[][] m = new double[d][d];
        for (int i = 0; i < v; i++) for (int j = 0; j < d; j++) e[i][j] = r.nextGaussian() * 0.08;
        for (int i = 0; i < d; i++) for (int j = 0; j < d; j++) m[i][j] = r.nextGaussian() * 0.08;
        return new AlignedAdapter(label, "S3", "S3", e, m);
    }

    private static EvalTask mkEvalTask(String id, int n, int k, int vocab, int d, long inputSeed, long expSeed) {
        Prng ri = new Prng(inputSeed);
        Prng re = new Prng(expSeed);
        int[][] inputs = new int[n][k];
        double[][] expected = new double[n][d];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < k; j++) inputs[i][j] = Math.floorMod(ri.nextLong(), vocab);
            for (int j = 0; j < d; j++) expected[i][j] = re.nextGaussian() * 0.12;
        }
        return new EvalTask(id, inputs, expected);
    }

    private static void checkClose(String tag, double[][] expected, double[][] actual, double tol) {
        if (actual == null) fail(tag + ": actual is null");
        if (expected.length != actual.length || expected[0].length != actual[0].length) {
            fail(tag + ": shape mismatch expected " + expected.length + "x" + expected[0].length
                    + " actual " + actual.length + "x" + actual[0].length);
        }
        double worst = 0.0;
        int wi = 0, wj = 0;
        for (int i = 0; i < expected.length; i++) {
            for (int j = 0; j < expected[0].length; j++) {
                double diff = Math.abs(expected[i][j] - actual[i][j]);
                if (diff > worst) { worst = diff; wi = i; wj = j; }
            }
        }
        if (worst > tol) {
            fail(tag + ": max abs diff " + worst + " at [" + wi + "," + wj
                    + "] expected=" + expected[wi][wj] + " actual=" + actual[wi][wj]);
        }
    }

    private static void fail(String msg) {
        System.err.println("VERIFY FAIL: " + msg);
        System.exit(1);
    }
}
