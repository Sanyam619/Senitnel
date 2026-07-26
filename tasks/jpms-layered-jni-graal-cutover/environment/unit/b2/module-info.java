module helix.spi {
  requires helix.api;
  exports io.helix.spi;
  provides io.helix.api.Slot with io.helix.spi.SlotProvider;
}
