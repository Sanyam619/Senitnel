package emitout;

public final class Main {
    public static void main(String[] args) throws Exception {
        int rc = forge.OpC.op_c(lib.Paths.TOKEN, lib.Paths.POLICY, lib.Paths.OUT);
        System.exit(rc == 0 ? 0 : 1);
    }
}
