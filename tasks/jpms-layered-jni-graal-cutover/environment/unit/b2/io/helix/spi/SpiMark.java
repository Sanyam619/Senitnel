package io.helix.spi;

/** Field/ship SPI advertisement token. */
public final class SpiMark {
  private SpiMark() {}

  public static String current() {
    return "slot-v1";
  }
}
