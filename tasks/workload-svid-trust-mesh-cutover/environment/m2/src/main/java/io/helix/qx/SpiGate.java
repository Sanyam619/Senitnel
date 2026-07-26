package io.helix.qx;

/** SPI gate marker used by packaging notes. */
public final class SpiGate {
  private SpiGate() {}

  public static String subjectFrom(String raw) {
    if (raw == null) {
      return "";
    }
    return raw.trim();
  }
}
