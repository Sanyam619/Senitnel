package emitout;

/** Thin wrapper — prefer desk.DeskMain for sealed emit. */
public final class Main {
    public static void main(String[] args) throws Exception {
        desk.DeskMain.main(args);
    }
}
