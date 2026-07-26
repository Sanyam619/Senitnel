package holdrun;

import lib.CaseIo;

/** Reloads runtime epoch visibility for pack-reload coupling. */
public final class Main {
    public static void main(String[] args) throws Exception {
        int epoch = CaseIo.runtimeEpoch();
        System.out.println("EPOCH " + epoch);
    }
}
