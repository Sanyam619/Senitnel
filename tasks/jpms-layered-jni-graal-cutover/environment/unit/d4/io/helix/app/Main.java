package io.helix.app;

import io.helix.api.Slot;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.ServiceLoader;

/**
 * Probe entry used by packctl launch modes. argv[0] = output json path,
 * argv[1] optional = hook FQCN for reflective JNI exercise.
 */
public final class Main {
  private Main() {}

  public static void main(String[] args) throws Exception {
    boolean spi = false;
    for (Slot s : ServiceLoader.load(Slot.class)) {
      if ("slot-v2".equals(s.tag())) {
        spi = true;
        break;
      }
    }
    String hook = args.length > 1 ? args[1] : "io.helix.bridge.NativeHook";
    boolean jni = false;
    int token = -1;
    try {
      Class<?> c = Class.forName(hook);
      Method tok = c.getMethod("token");
      token = (Integer) tok.invoke(null);
      Method ping = c.getMethod("ping", int.class);
      jni = ((Integer) ping.invoke(null, 3)) == 4;
    } catch (Throwable t) {
      jni = false;
    }
    Map<String, Object> out = new LinkedHashMap<>();
    out.put("spi_bound", spi);
    out.put("jni_bridge", jni);
    out.put("token", token);
    out.put("hook", hook);
    String json = toJson(out);
    if (args.length > 0) {
      Path p = Path.of(args[0]);
      if (p.getParent() != null) {
        Files.createDirectories(p.getParent());
      }
      Files.writeString(p, json, StandardCharsets.UTF_8);
    } else {
      System.out.print(json);
    }
  }

  private static String toJson(Map<String, Object> m) {
    List<String> parts = new ArrayList<>();
    for (Map.Entry<String, Object> e : m.entrySet()) {
      Object v = e.getValue();
      if (v instanceof Boolean || v instanceof Number) {
        parts.add("\"" + e.getKey() + "\":" + v);
      } else {
        parts.add("\"" + e.getKey() + "\":\"" + v + "\"");
      }
    }
    return "{" + String.join(",", parts) + "}";
  }
}
