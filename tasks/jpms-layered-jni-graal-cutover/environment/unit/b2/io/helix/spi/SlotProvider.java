package io.helix.spi;

import io.helix.api.Slot;

public final class SlotProvider implements Slot {
  @Override
  public String tag() {
    return SpiMark.current();
  }
}
