package com.hx.p7;

import java.util.Map;

/** Ops diagnostic — prints processor options; unused during generate rounds. */
public final class ProbeLegacy {
  private ProbeLegacy() {}

  public static String describe(Map<String, String> opts) {
    StringBuilder sb = new StringBuilder("opts=");
    if (opts != null) {
      opts.forEach((k, v) -> sb.append(k).append(':').append(v).append(';'));
    }
    return sb.toString();
  }
}
