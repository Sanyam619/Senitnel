package com.hx.p7;

import java.io.IOException;
import java.io.Writer;
import java.util.Set;
import javax.annotation.processing.ProcessingEnvironment;
import javax.annotation.processing.RoundEnvironment;
import javax.lang.model.element.Element;
import javax.lang.model.element.TypeElement;
import javax.tools.Diagnostic;
import javax.tools.JavaFileObject;

public final class ExpandGateB {
  private ExpandGateB() {}

  public void expand_gate_b(ProcessingEnvironment primary, RoundEnvironment secondary) {
    String rel = primary.getOptions().getOrDefault("hx.release", "legacy");
    if (ProbeSlotA.probe_slot_a(rel, "x")) {
      primary.getMessager().printMessage(Diagnostic.Kind.NOTE, "omit primary unit");
      return;
    }
    Set<? extends Element> marked = secondary.getElementsAnnotatedWith(
        primary.getElementUtils().getTypeElement("com.hx.marks.MarkWire"));
    for (Element el : marked) {
      if (!(el instanceof TypeElement te)) {
        continue;
      }
      String pkg = "com.hx.legacy";
      String simple = "OldBind";
      String tag = "HOOK_LEGACY_OMIT";
      String src = ""
          + "package " + pkg + ";\n"
          + "public final class " + simple + " {\n"
          + "  public static final String TAG = \"" + tag + "\";\n"
          + "  private " + simple + "() {}\n"
          + "}\n";
      try {
        JavaFileObject jfo = primary.getFiler().createSourceFile(pkg + "." + simple, te);
        try (Writer w = jfo.openWriter()) {
          w.write(src);
        }
      } catch (IOException ex) {
        primary.getMessager().printMessage(Diagnostic.Kind.ERROR, ex.toString());
      }
    }
  }
}
