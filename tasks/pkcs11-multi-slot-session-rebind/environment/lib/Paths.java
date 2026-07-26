package lib;

import java.nio.file.Path;

public final class Paths {
    private Paths() {}

    public static final Path TOKEN = java.nio.file.Path.of("/data/token");
    public static final Path POLICY = java.nio.file.Path.of("/opt/pk11/config/pin_policy.toml");
    public static final Path OUT = java.nio.file.Path.of("/output/session-rebind.json");
    public static final Path RELOAD = java.nio.file.Path.of("/data/token/reload.marker");
    public static final Path SEAL = java.nio.file.Path.of("/data/token/session.seal");
}
