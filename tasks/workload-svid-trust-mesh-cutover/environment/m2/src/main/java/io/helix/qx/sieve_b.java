package io.helix.qx;

import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Trust decision under live bundle + TrustManager cache semantics.
 * a: scenario json path; b: live-bundle json path
 */
public final class sieve_b {
  private sieve_b() {}

  public static String step(String a, String b) {
    try {
      String scenario = Files.readString(Path.of(a));
      String live = Files.readString(Path.of(b));
      String runtime = Files.readString(Path.of("/app/data/state/runtime.json"));
      String roots = Files.readString(Path.of("/app/data/material/roots.json"));
      String cache = Files.readString(Path.of("/app/data/state/tm-cache.json"));

      long asOf = ParseX.x_long(runtime, "as_of");
      String activeRoot = ParseX.x_str(live, "active_root");
      int liveEpoch = ParseX.x_int(live, "epoch");
      int liveGen = ParseX.x_int(live, "generation");

      String root = ParseX.x_str(scenario, "root");
      long notAfter = ParseX.x_long(scenario, "intermediate_not_after");
      long notBefore = ParseX.x_long(scenario, "intermediate_not_before");
      String subject = ParseX.x_str(scenario, "subject");
      String id = ParseX.x_str(scenario, "id");

      boolean warm = cache.contains("\"warm\": true") || cache.contains("\"warm\":true");
      String cacheRoot = ParseX.x_str(cache, "last_root");
      int cacheEpoch = ParseX.x_int(cache, "last_epoch");

      // Cached TrustManager: when warm and still bound to the scenario root,
      // intermediate not-after is not re-evaluated (stale manager semantics).
      boolean pinned = warm && root.equals(cacheRoot) && cacheEpoch > 0;

      if (!pinned) {
        if (notBefore > 0 && notBefore > asOf) {
          return "reject:inter_early";
        }
        if (notAfter < asOf) {
          return "reject:inter_expired";
        }
      }

      if (!root.equals(activeRoot)) {
        return "reject:root_stale";
      }

      int wantGen = ParseX.x_int_nested(roots, root, "generation");
      if (wantGen > 0 && liveGen > 0 && wantGen != liveGen) {
        return "reject:gen_skew";
      }

      String wantSubject = ParseX.x_str_by_root(roots, activeRoot);
      if (wantSubject.isEmpty()) {
        wantSubject = ParseX.x_str(roots, "spi_subject");
      }
      if (!subject.equals(wantSubject)) {
        return "reject:spi_mismatch";
      }
      if ("spi_bind".equals(id)) {
        return "accept:spi_ok";
      }
      return "accept:ok_fresh";
    } catch (Exception e) {
      return "reject:error";
    }
  }
}
