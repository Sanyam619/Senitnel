package com.archives.core.r8;

import com.archives.cfg.LaneCfg;
import com.archives.cfg.PropsLoader;
import com.archives.core.k9.LineageExpand;
import com.archives.core.k9.VolumeGraph;
import com.archives.engine.p3.MergeLane;
import com.archives.engine.q1.EvalCtx;
import com.archives.engine.q1.RulePack;
import com.archives.ingest.d4.CirculationParser;
import com.archives.ingest.d4.CirculationRow;
import com.archives.ingest.m7.RfidRow;
import com.archives.ingest.m7.RfidFold;
import com.archives.ingest.n2.QuarantineParser;
import com.archives.ingest.n2.QuarantineRow;
import com.archives.ingest.r3.SweepLoader;
import com.archives.ingest.s5.CovenantParser;
import com.archives.ingest.s5.CovenantRow;
import com.archives.ingest.v6.ExhibitParser;
import com.archives.ingest.v6.ExhibitRow;
import com.archives.io.JsonWriter;
import com.archives.io.TsvWriter;
import com.archives.model.AuditEntry;
import com.archives.model.OutRow;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class Orchestrator {
    public void execute(String day, String root) throws Exception {
        LaneCfg cfg = new PropsLoader().load();
        Path dayDir = Path.of(root, "days", day);
        Path outDir = Path.of(cfg.outRoot(), day);
        Files.createDirectories(outDir);

        List<QuarantineRow> notices = new QuarantineParser().read(dayDir.resolve("quarantine_feed.csv"));
        List<CovenantRow> signoffs = new CovenantParser().read(dayDir.resolve("covenant_feed.csv"));
        List<ExhibitRow> reviews = new ExhibitParser().read(dayDir.resolve("exhibit_feed.csv"));
        List<RfidRow> probes = RfidFold.read(dayDir.resolve("rfid_feed.csv"));
        List<CirculationRow> docks = new CirculationParser().read(dayDir.resolve("circulation_feed.csv"));
        SweepLoader.SweepMeta meta = new SweepLoader().read(dayDir.resolve("sweep_map.json"));

        List<RfidRow> folded = RfidFold.fold_a(probes, meta.hookTs(), meta.dockTs());
        Map<String, List<String>> splitMap = new VolumeGraph().splitsFromCirculation(docks);

        Map<String, QuarantineRow> noticeByUnit = indexNotice(notices, splitMap);
        Map<String, CovenantRow> signoffByUnit = indexSignoff(signoffs);
        Map<String, ExhibitRow> reviewByUnit = indexReview(reviews);
        Set<String> rfidVolumes = rfidVolumes(folded);

        List<OutRow> ledger = new ArrayList<>();
        List<AuditEntry> audit = new ArrayList<>();
        List<OutRow> affected = new ArrayList<>();
        int dayNum = dayHash(day);

        for (CirculationRow dock : docks) {
            String unit = dock.unitId();
            QuarantineRow notice = noticeForUnit(unit, noticeByUnit, splitMap);
            CovenantRow signoff = signoffByUnit.get(unit);
            ExhibitRow review = reviewByUnit.get(unit);
            String state = MergeLane.merge_b(notice, signoff, review);
            if (notice == null && !rfidVolumes.contains(unit)) {
                state = "DENIED_LOAN";
            }
            String reason = RulePack.reason(new EvalCtx(state, notice, review, rfidVolumes.contains(unit)));
            ledger.add(new OutRow(unit, state, reason, dayNum));
            if ("DENIED_LOAN".equals(state)) {
                affected.add(new OutRow(unit, dock.storeId(), reason, dock.qtyCases()));
            }
            if (signoff != null) {
                audit.add(new AuditEntry(unit, signoff.authId(), signoff.decision(), MergeLane.rank(signoff, notice)));
            }
        }

        new JsonWriter().writeLedger(outDir.resolve("loan_decision_ledger.jsonl"), ledger);
        new JsonWriter().writeAudit(outDir.resolve("quarantine_exceptions.json"), audit);
        new TsvWriter().write(outDir.resolve("shelf_custody_audit.tsv"), affected);
    }

    private static int dayHash(String day) {
        return Math.abs(day.hashCode() % 10000);
    }

    private static Map<String, QuarantineRow> indexNotice(List<QuarantineRow> notices, Map<String, List<String>> splitMap) {
        Map<String, QuarantineRow> out = new HashMap<>();
        for (QuarantineRow n : notices) {
            for (String u : LineageExpand.resolve_d(n.unitId(), splitMap)) {
                out.put(u, n);
            }
        }
        return out;
    }

    private static Map<String, CovenantRow> indexSignoff(List<CovenantRow> rows) {
        Map<String, CovenantRow> out = new HashMap<>();
        for (CovenantRow r : rows) {
            out.put(r.unitId(), r);
        }
        return out;
    }

    private static Map<String, ExhibitRow> indexReview(List<ExhibitRow> rows) {
        Map<String, ExhibitRow> out = new HashMap<>();
        for (ExhibitRow r : rows) {
            out.put(r.unitId(), r);
        }
        return out;
    }

    private static Set<String> rfidVolumes(List<RfidRow> folded) {
        Set<String> s = new HashSet<>();
        for (RfidRow p : folded) {
            s.add(p.unitId());
        }
        return s;
    }

    private static QuarantineRow noticeForUnit(String unit, Map<String, QuarantineRow> noticeByUnit, Map<String, List<String>> splitMap) {
        QuarantineRow direct = noticeByUnit.get(unit);
        if (direct != null) {
            return direct;
        }
        for (Map.Entry<String, List<String>> e : splitMap.entrySet()) {
            if (e.getValue().contains(unit)) {
                return noticeByUnit.get(e.getKey());
            }
        }
        return null;
    }
}
