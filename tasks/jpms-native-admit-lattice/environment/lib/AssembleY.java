package lib;

import forge.OpC;
import forge.PrefC;
import forge.RowZ;
import forge.SlotZ;
import forge.SkimZ;
import flux.PrefA;
import nest.OpB;
import nest.PrefB;
import nest.RowY;
import nest.SlotY;
import nest.SkimY;

import java.nio.file.Files;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class AssembleY {
    private AssembleY() {}

    public static List<Map<String, String>> evaluateAll() throws Exception {
        List<Map<String, Object>> cases = CaseIo.loadCases();
        Set<String> marks = CaseIo.loadMarks();
        int[] win = CaseIo.loadWindow();
        int durable = CaseIo.readBundleGen(Paths.ROOTS.resolve("disk.bundle"));
        int live = CaseIo.readBundleGen(Paths.ROOTS.resolve("live.bundle"));
        List<Map<String, String>> rows = new ArrayList<>();
        for (Map<String, Object> c : cases) {
            rows.add(evaluateOne(c, marks, win, durable, live));
        }
        return rows;
    }

    static Map<String, String> evaluateOne(
            Map<String, Object> c,
            Set<String> marks,
            int[] win,
            int durable,
            int live)
            throws Exception {
        String id = String.valueOf(c.get("id"));
        int claim = ((Number) c.get("claim")).intValue();
        int gen = ((Number) c.get("gen")).intValue();
        String tip = String.valueOf(c.get("tip"));

        SkimY.surfaceOk(id);
        SkimZ.warmOk(live);

        PathTok tok = PathTok.of(id);
        int packed = NativeBridge.nativeReadPack(tok.path);
        if (packed < 0) {
            return row(id, "reject", "bad_layer");
        }
        int pack = packed & 0xff;
        int mode = (packed >> 8) & 0xff;
        int knit = NativeBridge.nativeKnit(pack, mode, PrefA.rank(), PrefA.modeWant());
        boolean packOk = (knit & 0x1) == 1;

        RowY ry = new RowY(id, claim, marks.contains(id), PrefB.lo(), PrefB.hi());
        if (win != null && win.length == 2) {
            ry = new RowY(id, claim, marks.contains(id), win[0], win[1]);
        }
        SlotY sy = new SlotY();
        OpB.op_b(ry, sy);

        RowZ rz = new RowZ(gen, durable, live);
        if (PrefC.durableGen() > 0) {
            rz = new RowZ(gen, durable, live);
        }
        SlotZ sz = new SlotZ();
        OpC.op_c(rz, sz);

        String decision;
        String reason;
        if (!packOk) {
            decision = "reject";
            reason = "bad_layer";
        } else if (sy.code == 2) {
            decision = "reject";
            reason = "stale_reflect";
        } else if (sy.code == 1) {
            decision = "reject";
            reason = "revoked";
        } else if (sz.genOk != 1) {
            decision = "reject";
            reason = "hook_skew";
        } else {
            decision = "accept";
            reason = "ok_bound";
        }

        if (tip == null) {
            tip = id;
        }
        return row(id, decision, reason);
    }

    private static Map<String, String> row(String id, String decision, String reason) {
        Map<String, String> m = new LinkedHashMap<>();
        m.put("id", id);
        m.put("decision", decision);
        m.put("reason_code", reason);
        return m;
    }

    static final class PathTok {
        final String path;

        private PathTok(String path) {
            this.path = path;
        }

        static PathTok of(String id) {
            return new PathTok(Paths.TOKEN.resolve(id + ".tok").toString());
        }
    }
}
