package authcheck;

import java.lang.reflect.Method;

public final class Main {
    public static void main(String[] args) throws Exception {
        Class<?> gate = Class.forName("lib.Vx");
        Method m = gate.getMethod("gate");
        int rc = (Integer) m.invoke(null);
        System.exit(rc);
    }
}
