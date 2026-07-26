package packhold;

import lib.AssembleY;

import java.util.List;
import java.util.Map;

/** Re-entry probe: evaluates lattice without writing the ledger. */
public final class Main {
    public static void main(String[] args) throws Exception {
        List<Map<String, String>> rows = AssembleY.evaluateAll();
        int accepts = 0;
        for (Map<String, String> r : rows) {
            if ("accept".equals(r.get("decision"))) {
                accepts++;
            }
            System.out.println(r.get("id") + " " + r.get("decision") + " " + r.get("reason_code"));
        }
        System.out.println("HOLDS " + accepts);
    }
}
