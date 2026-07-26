package io.terminus.stitch.model;

/** Downstream evaluation task: token sequences with expected output vectors. */
public final class EvalTask {
    public final String taskId;
    public final int[][] inputs;
    public final double[][] expected;

    public EvalTask(String taskId, int[][] inputs, double[][] expected) {
        this.taskId = taskId;
        this.inputs = inputs;
        this.expected = expected;
    }
}
