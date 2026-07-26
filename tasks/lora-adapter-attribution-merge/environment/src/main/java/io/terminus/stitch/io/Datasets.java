package io.terminus.stitch.io;

import io.terminus.stitch.model.Adapter;
import io.terminus.stitch.model.EvalTask;
import io.terminus.stitch.model.Snapshot;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/** Loads snapshots / adapters / eval tasks from JSON on disk. */
public final class Datasets {
    private Datasets() {}

    public static Map<String, Snapshot> loadAllSnapshots(Path dir) throws IOException {
        TreeMap<String, Snapshot> out = new TreeMap<>();
        try (var stream = Files.list(dir)) {
            for (Path p : (Iterable<Path>) stream.filter(x -> x.getFileName().toString().endsWith(".json"))::iterator) {
                Snapshot s = loadSnapshot(p);
                out.put(s.id, s);
            }
        }
        return out;
    }

    public static Snapshot loadSnapshot(Path p) throws IOException {
        String text = Files.readString(p);
        Map<String, Object> obj = JsonReader.asObject(JsonReader.parse(text));
        String id = JsonReader.asString(obj.get("id"));
        int vocabSize = JsonReader.asInt(obj.get("vocab_size"));
        int embedDim = JsonReader.asInt(obj.get("embed_dim"));
        double[][] embedding = JsonReader.asMatrix(obj.get("embedding"));
        double[][] mlpWeight = JsonReader.asMatrix(obj.get("mlp_weight"));
        double rmsEps = JsonReader.asDouble(obj.get("rms_eps"));
        double cal = JsonReader.asDouble(obj.get("cal_mean_sq"));
        return new Snapshot(id, vocabSize, embedDim, embedding, mlpWeight, rmsEps, cal);
    }

    public static List<Adapter> loadAllAdapters(Path dir) throws IOException {
        java.util.ArrayList<Adapter> out = new java.util.ArrayList<>();
        // Sorted for determinism.
        try (var stream = Files.list(dir)) {
            java.util.List<Path> paths = new java.util.ArrayList<>();
            stream.filter(x -> x.getFileName().toString().endsWith(".json")).forEach(paths::add);
            paths.sort(java.util.Comparator.comparing(x -> x.getFileName().toString()));
            for (Path p : paths) out.add(loadAdapter(p));
        }
        return out;
    }

    public static Adapter loadAdapter(Path p) throws IOException {
        String text = Files.readString(p);
        Map<String, Object> obj = JsonReader.asObject(JsonReader.parse(text));
        String label = JsonReader.asString(obj.get("label"));
        String src = JsonReader.asString(obj.get("source_snapshot"));
        int rank = JsonReader.asInt(obj.get("rank"));
        double[][] eA = JsonReader.asMatrix(obj.get("embed_A"));
        double[][] eB = JsonReader.asMatrix(obj.get("embed_B"));
        double[][] mA = JsonReader.asMatrix(obj.get("mlp_A"));
        double[][] mB = JsonReader.asMatrix(obj.get("mlp_B"));
        return new Adapter(label, src, rank, eA, eB, mA, mB);
    }

    public static List<EvalTask> loadAllEvalTasks(Path dir) throws IOException {
        java.util.ArrayList<EvalTask> out = new java.util.ArrayList<>();
        try (var stream = Files.list(dir)) {
            java.util.List<Path> paths = new java.util.ArrayList<>();
            stream.filter(x -> x.getFileName().toString().endsWith(".json")).forEach(paths::add);
            paths.sort(java.util.Comparator.comparing(x -> x.getFileName().toString()));
            for (Path p : paths) out.add(loadEvalTask(p));
        }
        return out;
    }

    public static EvalTask loadEvalTask(Path p) throws IOException {
        String text = Files.readString(p);
        Map<String, Object> obj = JsonReader.asObject(JsonReader.parse(text));
        String taskId = JsonReader.asString(obj.get("task_id"));
        List<Object> inputRows = JsonReader.asArray(obj.get("inputs"));
        int[][] inputs = new int[inputRows.size()][];
        for (int i = 0; i < inputRows.size(); i++) inputs[i] = JsonReader.asIntArray(inputRows.get(i));
        double[][] expected = JsonReader.asMatrix(obj.get("expected"));
        return new EvalTask(taskId, inputs, expected);
    }
}
