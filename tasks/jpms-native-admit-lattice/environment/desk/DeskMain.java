package desk;

import flux.PrefA;
import forge.PrefC;
import gate.GateSeal;
import lib.AssembleY;
import lib.CaseIo;
import lib.JsonOut;
import lib.Paths;
import nest.PrefB;

import java.nio.file.Files;
import java.util.List;
import java.util.Map;

public final class DeskMain {
    public static void main(String[] args) throws Exception {
        boolean surface = args.length > 0 && "--surface".equals(args[0]);
        if (surface) {
            System.out.println("SURFACE_OK");
            return;
        }

        if (!GateSeal.prefsMatch(
                PrefA.rank(), PrefA.modeWant(), PrefC.durableGen(), PrefB.lo(), PrefB.hi())) {
            System.err.println("GATE_REJECT prefs");
            System.exit(2);
        }

        List<Map<String, String>> rows = AssembleY.evaluateAll();
        int epoch = CaseIo.runtimeEpoch();
        JsonOut.writeLedger(epoch, rows);
        Files.writeString(Paths.GATE_STAMP, "pack-emit-ok\n");
        System.out.println("EMIT_OK " + rows.size());
    }
}
