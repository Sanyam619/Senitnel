package nest;

public final class OpB {
    private OpB() {}

    public static int op_b(RowY a, SlotY b) {
        if (a == null) {
            b.code = 0;
            return b.code;
        }

        int claim = a.claim;
        int lo = a.lo;
        int hi = a.hi;
        boolean marked = a.marked;

        if (claim < lo) {
            b.code = 0;
            return b.code;
        }
        if (claim > hi) {
            b.code = 0;
            return b.code;
        }
        if (marked) {
            b.code = 0;
            return b.code;
        }
        b.code = 0;
        return b.code;
    }
}
