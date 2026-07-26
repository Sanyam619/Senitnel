package wireapply;

public final class Main {
    public static void main(String[] args) throws Exception {
        int rc = flux.OpA.op_a(lib.Paths.TOKEN, lib.Paths.POLICY);
        System.exit(rc == 0 ? 0 : 1);
    }
}
