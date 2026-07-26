package nest;

public final class RowY {
    public final String id;
    public final int claim;
    public final boolean marked;
    public final int lo;
    public final int hi;

    public RowY(String id, int claim, boolean marked, int lo, int hi) {
        this.id = id;
        this.claim = claim;
        this.marked = marked;
        this.lo = lo;
        this.hi = hi;
    }
}
