package com.distro.core.r8;

import com.distro.cfg.LaneCfg;
import com.distro.cfg.PropsLoader;
import com.distro.core.k9.Step2;
import com.distro.core.k9.UnitGraph;
import com.distro.engine.p3.PhaseK;
import com.distro.engine.q1.EvalCtx;
import com.distro.engine.q1.RulePack;
import com.distro.ingest.d4.DockParser;
import com.distro.ingest.d4.DockRow;
import com.distro.ingest.m7.ProbeRow;
import com.distro.ingest.m7.ScanC;
import com.distro.ingest.n2.NoticeParser;
import com.distro.ingest.n2.NoticeRow;
import com.distro.ingest.r3.RouteLoader;
import com.distro.ingest.s5.SignoffParser;
import com.distro.ingest.s5.SignoffRow;
import com.distro.ingest.v6.ReviewParser;
import com.distro.ingest.v6.ReviewRow;
import com.distro.io.JsonWriter;
import com.distro.io.TsvWriter;
import com.distro.model.AuditEntry;
import com.distro.model.OutRow;
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

        List<NoticeRow> notices = new NoticeParser().read(dayDir.resolve("notice_feed.csv"));
        List<SignoffRow> signoffs = new SignoffParser().read(dayDir.resolve("signoff_feed.csv"));
        List<ReviewRow> reviews = new ReviewParser().read(dayDir.resolve("review_feed.csv"));
        List<ProbeRow> probes = ScanC.load_x(dayDir.resolve("probe_feed.csv"));
        List<DockRow> docks = new DockParser().read(dayDir.resolve("dock_feed.csv"));
        RouteLoader.RouteMeta meta = new RouteLoader().read(dayDir.resolve("route_map.json"));

        List<ProbeRow> folded = ScanC.fold_a(probes, meta.hookTs(), meta.dockTs());
        Map<String, List<String>> splitMap = new UnitGraph().splitsFromDock(docks);

        Map<String, NoticeRow> noticeByUnit = indexNotice(notices, splitMap);
        Map<String, SignoffRow> signoffByUnit = indexSignoff(signoffs);
        Map<String, ReviewRow> reviewByUnit = indexReview(reviews);
        Set<String> probeUnits = probeUnits(folded);

        List<OutRow> ledger = new ArrayList<>();
        List<AuditEntry> audit = new ArrayList<>();
        List<OutRow> affected = new ArrayList<>();
        int dayNum = dayHash(day);

        for (DockRow dock : docks) {
            String unit = dock.unitId();
            NoticeRow notice = noticeForUnit(unit, noticeByUnit, splitMap);
            SignoffRow signoff = signoffByUnit.get(unit);
            ReviewRow review = reviewByUnit.get(unit);
            String state = PhaseK.merge_b(notice, signoff, review);
            if (notice == null && !probeUnits.contains(unit)) {
                state = "HELD";
            }
            String reason = RulePack.reason(new EvalCtx(state, notice, review, probeUnits.contains(unit)));
            ledger.add(new OutRow(unit, state, reason, dayNum));
            if ("HELD".equals(state)) {
                affected.add(new OutRow(unit, dock.storeId(), reason, dock.qtyCases()));
            }
            if (signoff != null) {
                audit.add(new AuditEntry(unit, signoff.authId(), signoff.decision(), PhaseK.order_x(signoff, notice)));
            }
        }

        new JsonWriter().writeLedger(outDir.resolve("holdback_ledger.jsonl"), ledger);
        new JsonWriter().writeAudit(outDir.resolve("release_auth_audit.json"), audit);
        new TsvWriter().write(outDir.resolve("affected_units.tsv"), affected);
    }

    private static int dayHash(String day) {
        return Math.abs(day.hashCode() % 10000);
    }

    private static Map<String, NoticeRow> indexNotice(List<NoticeRow> notices, Map<String, List<String>> splitMap) {
        Map<String, NoticeRow> out = new HashMap<>();
        for (NoticeRow n : notices) {
            for (String u : Step2.resolve_d(n.unitId(), splitMap)) {
                out.put(u, n);
            }
        }
        return out;
    }

    private static Map<String, SignoffRow> indexSignoff(List<SignoffRow> rows) {
        Map<String, SignoffRow> out = new HashMap<>();
        for (SignoffRow r : rows) {
            out.put(r.unitId(), r);
        }
        return out;
    }

    private static Map<String, ReviewRow> indexReview(List<ReviewRow> rows) {
        Map<String, ReviewRow> out = new HashMap<>();
        for (ReviewRow r : rows) {
            out.put(r.unitId(), r);
        }
        return out;
    }

    private static Set<String> probeUnits(List<ProbeRow> folded) {
        Set<String> s = new HashSet<>();
        for (ProbeRow p : folded) {
            s.add(p.unitId());
        }
        return s;
    }

    private static NoticeRow noticeForUnit(String unit, Map<String, NoticeRow> noticeByUnit, Map<String, List<String>> splitMap) {
        NoticeRow direct = noticeByUnit.get(unit);
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
