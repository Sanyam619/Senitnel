package io.helix.qx;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** Rebinds TrustManager cache to the live bundle (ops entry). */
public final class TmRebind {
  private TmRebind() {}

  public static void main(String[] args) throws Exception {
    String livePath = args.length > 0 ? args[0] : "/app/data/state/live-bundle.json";
    String cachePath = args.length > 1 ? args[1] : "/app/data/state/tm-cache.json";
    String live = Files.readString(Path.of(livePath));
    String root = ParseX.x_str(live, "active_root");
    int epoch = ParseX.x_int(live, "epoch");
    String cache = "{\"warm\": false, \"last_root\": \"" + root
        + "\", \"last_epoch\": " + epoch + "}";
    Files.writeString(Path.of(cachePath), cache, StandardCharsets.UTF_8);
    System.out.println("tmrebind: ok");
  }
}
