package lib;

import java.nio.file.Path;

public final class Paths {
    private Paths() {}

    public static final Path APP = Path.of("/app");
    public static final Path CASES = APP.resolve("data/cases");
    public static final Path TOKEN = APP.resolve("data/token");
    public static final Path REVOKE = APP.resolve("data/revoke");
    public static final Path ROOTS = APP.resolve("data/roots");
    public static final Path RUNTIME = APP.resolve("data/state/runtime.json");
    public static final Path OUTPUT = Path.of("/output/pack-admit.json");
    public static final Path GATE_STAMP = Path.of("/output/.desk-stamp");
}
