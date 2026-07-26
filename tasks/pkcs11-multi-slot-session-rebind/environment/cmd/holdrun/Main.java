package holdrun;

public final class Main {
    public static void main(String[] args) throws Exception {
        int ttl = lib.TokenIo.readPolicyTtl(lib.Paths.POLICY);
        int rc = nest.OpB.op_b(lib.Paths.TOKEN, lib.Paths.RELOAD, ttl);
        System.exit(rc == 0 ? 0 : 1);
    }
}
