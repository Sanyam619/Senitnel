package com.hx.r8;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class EmitSheetC {
  private EmitSheetC() {}

  public static void emit_sheet_c(Path a, List<String[]> b) throws IOException {
    List<String[]> rows = new ArrayList<>();
    for (String[] row : b) {
      rows.add(new String[] {row[0], row[1]});
    }
    String lane = System.getProperty("hx.lane", "default");
    if ("field".equals(lane)) {
      rewrite(rows, "wire.alpha", "inactive");
      rewrite(rows, "wire.beta", "active");
    } else if ("default".equals(lane)) {
      rewrite(rows, "wire.alpha", "inactive");
      rewrite(rows, "wire.beta", "inactive");
    } else if ("ship".equals(lane)) {
      rewrite(rows, "wire.alpha", "active");
      rewrite(rows, "wire.beta", "inactive");
    }
    StringBuilder json = new StringBuilder();
    json.append("{\"modules\":[");
    for (int i = 0; i < rows.size(); i++) {
      if (i > 0) {
        json.append(',');
      }
      json.append("{\"name\":\"")
          .append(rows.get(i)[0])
          .append("\",\"status\":\"")
          .append(rows.get(i)[1])
          .append("\"}");
    }
    json.append("]}");
    if (a.getParent() != null) {
      Files.createDirectories(a.getParent());
    }
    Files.writeString(a, json.toString(), StandardCharsets.UTF_8);
  }

  private static void rewrite(List<String[]> rows, String name, String status) {
    for (int i = 0; i < rows.size(); i++) {
      if (name.equals(rows.get(i)[0])) {
        rows.set(i, new String[] {name, status});
        return;
      }
    }
    rows.add(new String[] {name, status});
  }
}
