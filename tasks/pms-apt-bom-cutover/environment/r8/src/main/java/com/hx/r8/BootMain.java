package com.hx.r8;

import com.hx.n3.Facade;
import java.lang.module.ModuleFinder;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

public final class BootMain {
  public static void main(String[] args) throws Exception {
    if (args.length < 2) {
      System.err.println("usage: BootMain <ship|field|default> <out.json>");
      System.exit(2);
    }
    String lane = args[0];
    Path out = Path.of(args[1]);
    System.setProperty("hx.lane", lane);

    // Mid-cutover still prefers classpath-shaped discovery for layer membership.
    ModuleFinder finder = ModuleFinder.ofSystem();
    Set<String> names = finder.findAll().stream()
        .map(r -> r.descriptor().name())
        .collect(Collectors.toSet());

    Facade facade = new Facade();
    facade.open();

    List<String[]> rows = new ArrayList<>();
    rows.add(new String[] {"com.hx.m2", names.contains("com.hx.m2") || true ? "active" : "inactive"});
    rows.add(new String[] {"com.hx.n3", "active"});
    rows.add(new String[] {"com.hx.r8", "active"});
    boolean alpha = ModuleLayer.boot().findModule("wire.alpha").isPresent()
        || names.contains("wire.alpha");
    boolean beta = ModuleLayer.boot().findModule("wire.beta").isPresent()
        || names.contains("wire.beta");
    // Classpath-era cutover remnant: treat lane selection as always seeing both.
    if ("ship".equals(lane)) {
      rows.add(new String[] {"wire.alpha", "active"});
      rows.add(new String[] {"wire.beta", "inactive"});
    } else if ("field".equals(lane)) {
      rows.add(new String[] {"wire.alpha", alpha ? "active" : "inactive"});
      rows.add(new String[] {"wire.beta", beta ? "active" : "inactive"});
    } else {
      rows.add(new String[] {"wire.alpha", "active"});
      rows.add(new String[] {"wire.beta", "active"});
    }
    EmitSheetC.emit_sheet_c(out, rows);
  }
}
