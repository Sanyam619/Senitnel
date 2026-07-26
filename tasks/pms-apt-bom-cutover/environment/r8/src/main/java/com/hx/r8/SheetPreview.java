package com.hx.r8;

import java.util.List;

/** Docs dry-run pretty printer; not invoked by ship/field launcher. */
public final class SheetPreview {
  private SheetPreview() {}

  public static String pretty(List<String[]> rows) {
    StringBuilder sb = new StringBuilder();
    for (String[] row : rows) {
      sb.append(row[0]).append('=').append(row[1]).append('
');
    }
    return sb.toString();
  }
}
