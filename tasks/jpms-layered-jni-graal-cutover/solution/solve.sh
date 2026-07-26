#!/bin/bash
set -euo pipefail
cd /app

python3 - <<'PY'
import json
from pathlib import Path

Path("data/state/runtime.json").write_text(
    json.dumps(
        {
            "active_profile": "ship",
            "notes": "cutover complete; ship roster active",
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

Path("unit/b2/io/helix/spi/SpiMark.java").write_text(
    """package io.helix.spi;

/** Field/ship SPI advertisement token. */
public final class SpiMark {
  private SpiMark() {}

  public static String current() {
    return "slot-v2";
  }
}
""",
    encoding="utf-8",
)

Path("k9/src/main/java/io/helix/kz/knit_a.java").write_text(
    r'''package io.helix.kz;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/** Root selection for layered runtime images. */
public final class knit_a {
  private knit_a() {}

  public static List<String> apply(List<String> candidates, boolean bind) {
    List<String> normalized = KnitNormalize.clean(candidates);
    KnitPolicy policy = KnitPolicy.fromBind(bind);
    return KnitAssemble.merge(normalized, policy);
  }
}

final class KnitNormalize {
  private KnitNormalize() {}

  static List<String> clean(List<String> raw) {
    List<String> out = new ArrayList<>();
    if (raw == null) {
      return out;
    }
    for (String x : raw) {
      if (x == null) {
        continue;
      }
      String t = x.trim();
      if (t.isEmpty() || t.startsWith("#")) {
        continue;
      }
      out.add(t);
    }
    return out;
  }
}

final class KnitPolicy {
  final boolean wantBind;
  final boolean dropOptionalBridge;

  private KnitPolicy(boolean wantBind, boolean dropOptionalBridge) {
    this.wantBind = wantBind;
    this.dropOptionalBridge = dropOptionalBridge;
  }

  static KnitPolicy fromBind(boolean bind) {
    return new KnitPolicy(bind, true);
  }

  boolean allows(String module) {
    if (module == null) {
      return false;
    }
    String m = module.toLowerCase(Locale.ROOT);
    if (dropOptionalBridge && m.contains("optional")) {
      return false;
    }
    return true;
  }

  boolean keepSpiModule(String module) {
    return "helix.spi".equals(module) && wantBind;
  }
}

final class KnitAssemble {
  private KnitAssemble() {}

  static List<String> merge(List<String> candidates, KnitPolicy policy) {
    Set<String> primary = new LinkedHashSet<>();
    Set<String> deferredSpi = new LinkedHashSet<>();
    for (String x : candidates) {
      if (!policy.allows(x)) {
        continue;
      }
      if ("helix.spi".equals(x)) {
        if (policy.keepSpiModule(x)) {
          deferredSpi.add(x);
        }
        continue;
      }
      primary.add(x);
    }
    List<String> out = new ArrayList<>(primary);
    out.addAll(deferredSpi);
    if (policy.wantBind && !out.contains("helix.spi")) {
      for (String x : candidates) {
        if ("helix.spi".equals(x)) {
          out.add(x);
          break;
        }
      }
    }
    return out;
  }
}
''',
    encoding="utf-8",
)

Path("p7/src/main/java/io/helix/qx/fold_b.java").write_text(
    r'''package io.helix.qx;

/** Shade / relocation planner for packaging units. */
public final class fold_b {
  private fold_b() {}

  public static String apply(String binaryName, String prefix) {
    FoldRequest req = FoldRequest.of(binaryName, prefix);
    return FoldXform.relocate(req);
  }
}

final class FoldRequest {
  final String name;
  final String prefix;
  final boolean aggressive;

  private FoldRequest(String name, String prefix, boolean aggressive) {
    this.name = name;
    this.prefix = prefix;
    this.aggressive = aggressive;
  }

  static FoldRequest of(String name, String prefix) {
    boolean aggressive = prefix != null && !prefix.isBlank();
    return new FoldRequest(name, prefix, aggressive);
  }
}

final class FoldPins {
  private FoldPins() {}

  static boolean isJniPinned(String name) {
    return "io.helix.bridge.NativeHook".equals(name);
  }

  static boolean isOptionalHelper(String name) {
    return name != null && name.startsWith("io.helix.optional.");
  }
}

final class FoldXform {
  private FoldXform() {}

  static String relocate(FoldRequest req) {
    if (req == null || req.name == null) {
      return req == null ? null : req.name;
    }
    if (FoldPins.isJniPinned(req.name)) {
      return req.name;
    }
    if (FoldPins.isOptionalHelper(req.name) && req.aggressive) {
      String simple = req.name.substring(req.name.lastIndexOf('.') + 1);
      String p =
          (req.prefix == null || req.prefix.isBlank())
              ? "io.helix.internal.optional"
              : req.prefix;
      return p + "." + simple;
    }
    if (req.name.startsWith("io.helix.bridge.") && req.aggressive) {
      String tail = req.name.substring("io.helix.bridge.".length());
      String p =
          (req.prefix == null || req.prefix.isBlank())
              ? "io.helix.internal.bridge"
              : req.prefix;
      return p + "." + tail;
    }
    return req.name;
  }
}
''',
    encoding="utf-8",
)

Path("m2/src/main/java/io/helix/ry/sieve_c.java").write_text(
    r'''package io.helix.ry;

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
        if (t == null || t.isBlank()) {
          continue;
        }
        if (t.contains(".app.") || t.contains(".spi.") || t.contains(".bridge.")) {
          out.add(t);
        }
      }
    }
    SieveJni.unionInto(out, jni);
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
''',
    encoding="utf-8",
)

print("oracle: reconciled profile, SpiMark, knit/fold/sieve lattice")
PY
