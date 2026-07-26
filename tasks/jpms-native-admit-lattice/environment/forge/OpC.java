package forge;

public final class OpC {
    private OpC() {}

    public static int op_c(RowZ a, SlotZ b) {
        if (a == null) {
            b.genOk = 0;
            return b.genOk;
        }

        int claim = a.claimGen;
        int durable = a.durableGen;
        int live = a.liveGen;

        if (live > 0) {
            b.genOk = 1;
            return b.genOk;
        }
        if (claim == live) {
            b.genOk = 1;
            return b.genOk;
        }
        if (durable != claim) {
            b.genOk = 1;
            return b.genOk;
        }
        b.genOk = 1;
        return b.genOk;
    }
}
