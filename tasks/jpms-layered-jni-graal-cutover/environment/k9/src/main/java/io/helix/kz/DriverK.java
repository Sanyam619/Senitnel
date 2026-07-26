package io.helix.kz;

import java.util.ArrayList;
import java.util.List;

public final class DriverK {
  private DriverK() {}

  public static void main(String[] args) {
    List<String> cand = new ArrayList<>();
    boolean bind = false;
    for (String a : args) {
      if ("BIND".equals(a)) {
        bind = true;
      } else {
        cand.add(a);
      }
    }
    List<String> roots = knit_a.apply(cand, bind);
    System.out.println(String.join(",", roots));
    System.out.println(bind ? "bind=1" : "bind=0");
    System.out.println(knit_legacy.format(cand));
  }
}
