package com.acme.ops;

import java.nio.file.Path;

public final class Console {
    public static void main(String[] args) throws Exception {
        Path input = args.length > 0 ? Path.of(args[0]) : Path.of("/app/scenarios");
        Path output = args.length > 1 ? Path.of(args[1]) : Path.of("/app/output");
        ProcessBuilder pb = new ProcessBuilder(
                "bash",
                "/app/ops/tools/replay.sh",
                input.toString(),
                output.toString());
        pb.inheritIO();
        int code = pb.start().waitFor();
        if (code != 0) {
            System.exit(code);
        }
    }
}
