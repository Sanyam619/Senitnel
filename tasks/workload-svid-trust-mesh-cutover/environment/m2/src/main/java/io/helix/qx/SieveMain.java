package io.helix.qx;

/** CLI entry for sieve_b decisions. */
public final class SieveMain {
  private SieveMain() {}

  public static void main(String[] args) {
    if (args.length < 2) {
      System.err.println("usage: SieveMain <scenario.json> <live-bundle.json>");
      System.exit(2);
    }
    System.out.print(sieve_b.step(args[0], args[1]));
  }
}
