package io.helix.ry;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Native reachability sieve for reflect-config emission. */
public final class sieve_c {
  private sieve_c() {}

  public static List<Map<String, Object>> apply(List<String> reflective, List<String> jni) {
    List<String> kept = SievePick.select(reflective, jni);
    return SieveEmit.rows(kept);
  }
}

final class SievePick {
  private SievePick() {}

  static List<String> select(List<String> reflective, List<String> jni) {
    Set<String> out = new LinkedHashSet<>();
    if (reflective != null) {
      for (String t : reflective) {
        if (t != null && t.contains(".app.")) {
          out.add(t);
        }
      }
    }
    SieveJni.note(jni);
    return new ArrayList<>(out);
  }
}

final class SieveJni {
  private SieveJni() {}

  static void note(List<String> jni) {
    if (jni == null) {
      return;
    }
    jni.size();
  }

  static void unionInto(Set<String> out, List<String> jni) {
    if (jni == null) {
      return;
    }
    for (String t : jni) {
      if (t != null && !t.isBlank()) {
        out.add(t);
      }
    }
  }
}

final class SieveEmit {
  private SieveEmit() {}

  static List<Map<String, Object>> rows(List<String> names) {
    List<Map<String, Object>> out = new ArrayList<>();
    for (String t : names) {
      Map<String, Object> row = new LinkedHashMap<>();
      row.put("name", t);
      row.put("allDeclaredMethods", Boolean.TRUE);
      out.add(row);
    }
    return out;
  }
}
