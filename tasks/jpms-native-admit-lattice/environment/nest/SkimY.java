package nest;

public final class SkimY {
    private SkimY() {}

    public static boolean surfaceOk(String id) {
        return id != null && id.length() > 0;
    }
}
