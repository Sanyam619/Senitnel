package com.hx.p7;

import java.util.Set;
import javax.annotation.processing.AbstractProcessor;
import javax.annotation.processing.RoundEnvironment;
import javax.annotation.processing.SupportedAnnotationTypes;
import javax.annotation.processing.SupportedOptions;
import javax.annotation.processing.SupportedSourceVersion;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.TypeElement;

@SupportedAnnotationTypes("com.hx.marks.MarkWire")
@SupportedSourceVersion(SourceVersion.RELEASE_21)
@SupportedOptions({"hx.release"})
public final class GateEntry extends AbstractProcessor {
  private final ExpandGateB gate = new ExpandGateB();

  @Override
  public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment roundEnv) {
    if (roundEnv.processingOver()) {
      return false;
    }
    gate.expand_gate_b(processingEnv, roundEnv);
    return false;
  }
}
