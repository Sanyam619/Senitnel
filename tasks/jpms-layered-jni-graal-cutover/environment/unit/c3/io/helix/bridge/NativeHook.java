package io.helix.bridge;

public final class NativeHook {
  static {
    System.loadLibrary("helixhook");
  }

  private NativeHook() {}

  public static native int ping(int x);

  public static int token() {
    return 17;
  }
}
