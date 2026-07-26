package lib;

public final class NativeBridge {
    static {
        System.load("/opt/desk/lib/libpackjni.so");
    }

    private NativeBridge() {}

    public static native int nativeKnit(int pack, int mode, int wantRank, int wantMode);

    public static native long nativeSkim(byte[] buf);

    public static native int nativeReadPack(String path);
}
