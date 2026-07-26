#!/usr/bin/env python3
"""Generate food-recall-cold-chain-holdback task files."""
from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "food-recall-cold-chain-holdback"
ENV = ROOT / "environment"


def w(rel: str, content: str) -> None:
    p = ROOT / rel if not rel.startswith("environment/") else ENV / rel.removeprefix("environment/")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def main() -> None:
    w(
        "instruction.md",
        """
        Regional grocery distribution runs a Java batch job from `/opt/distro/scripts/run-cycle.sh`
        with `--day <distribution-day>` and `--root /data/fixtures`. It ingests notice feeds, probe
        feeds, dock feeds, review feeds, signoff feeds, and route maps, then writes
        `holdback_ledger.jsonl`, `release_auth_audit.json`, and `affected_units.tsv` under
        `/data/out/<day>/`.

        Since the latest policy rollout, recalled dairy units still show as releasable at stores
        that already captured signoff records, while unrelated frozen units stay blocked. Probe
        excursions QA cleared with signoff remain locked. Dock splits leave sibling child units
        moving when the parent unit was flagged, and reruns on those days inflate affected-unit
        counts.

        Rebuild the Maven project under `/opt/distro`, rerun the cycle for each distribution day,
        and leave fixtures under `/data/fixtures` unchanged. Distribution days are `day_r0412`
        through `day_r0416`.
        """,
    )

    w(
        "task.toml",
        """
        version = "2.0"

        [metadata]
        author_name = "anonymous"
        author_email = "anonymous"
        difficulty = "hard"
        category = "security"
        subcategories = []
        number_of_milestones = 0
        codebase_size = "small"
        languages = ["java", "bash"]
        tags = ["java", "food-safety", "cold-chain", "recall", "compliance", "batch"]
        expert_time_estimate_min = 120
        junior_time_estimate_min = 240

        [verifier]
        timeout_sec = 600

        [agent]
        timeout_sec = 900

        [environment]
        allow_internet = false
        build_timeout_sec = 900
        cpus = 2
        memory_mb = 4096
        storage_mb = 10240
        """,
    )

    w(
        "output_contract.toml",
        """
        user_visible_outputs = [
          "/data/out/<day>/holdback_ledger.jsonl",
          "/data/out/<day>/release_auth_audit.json",
          "/data/out/<day>/affected_units.tsv",
        ]

        internal_harness_files = [
          "/data/fixtures/days/",
        ]

        [structured_outputs.holdback_ledger]
        target = "/data/out/<day>/holdback_ledger.jsonl"
        format = "jsonl"
        instruction_checks = ["unit_id", "state", "reason_code", "source_day"]

        [structured_outputs.release_auth_audit]
        target = "/data/out/<day>/release_auth_audit.json"
        format = "json"
        instruction_checks = ["version", "entries"]

        [structured_outputs.affected_units]
        target = "/data/out/<day>/affected_units.tsv"
        format = "tsv"
        instruction_checks = ["unit_id", "store_id", "exposure_class", "qty_cases"]
        """,
    )

    w(
        "environment/.dockerignore",
        """
        target/
        .mvn/
        """,
    )

    w(
        "environment/pom.xml",
        """
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
          <modelVersion>4.0.0</modelVersion>
          <groupId>com.distro</groupId>
          <artifactId>cycle-batch</artifactId>
          <version>1.0.0</version>
          <properties>
            <maven.compiler.source>17</maven.compiler.source>
            <maven.compiler.target>17</maven.compiler.target>
            <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
          </properties>
          <build>
            <plugins>
              <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-jar-plugin</artifactId>
                <version>3.3.0</version>
                <configuration>
                  <archive>
                    <manifest>
                      <mainClass>com.distro.App</mainClass>
                    </manifest>
                  </archive>
                </configuration>
              </plugin>
            </plugins>
          </build>
        </project>
        """,
    )

    w("environment/config/lab.properties", "lane.prefix=DISTRO\nout.root=/data/out\n")

    w(
        "environment/scripts/run-cycle.sh",
        """
        #!/usr/bin/env bash
        set -euo pipefail
        DAY=""
        ROOT="/data/fixtures"
        while [[ $# -gt 0 ]]; do
          case "$1" in
            --day) DAY="$2"; shift 2 ;;
            --root) ROOT="$2"; shift 2 ;;
            *) echo "unknown arg: $1" >&2; exit 2 ;;
          esac
        done
        if [[ -z "$DAY" ]]; then
          echo "usage: run-cycle.sh --day <name> [--root /data/fixtures]" >&2
          exit 2
        fi
        java -jar /opt/distro/target/cycle-batch-1.0.0.jar "$DAY" "$ROOT"
        """,
    )

    w(
        "environment/scripts/build_fixtures.sh",
        FIXTURES_SH,
    )

    java_files = {
        "src/main/java/com/distro/App.java": APP_JAVA,
        "src/main/java/com/distro/CycleCmd.java": CYCLE_CMD_JAVA,
        "src/main/java/com/distro/cfg/PropsLoader.java": PROPS_LOADER,
        "src/main/java/com/distro/cfg/LaneCfg.java": LANE_CFG,
        "src/main/java/com/distro/core/k9/Step2.java": STEP2_BUG,
        "src/main/java/com/distro/core/k9/UnitGraph.java": UNIT_GRAPH,
        "src/main/java/com/distro/core/k9/LegacyBind.java": LEGACY_BIND,
        "src/main/java/com/distro/core/r8/Orchestrator.java": ORCHESTRATOR,
        "src/main/java/com/distro/core/r8/BatchCtx.java": BATCH_CTX,
        "src/main/java/com/distro/core/r8/StageGate.java": STAGE_GATE,
        "src/main/java/com/distro/ingest/m7/ScanC.java": SCAN_C_BUG,
        "src/main/java/com/distro/ingest/m7/ProbeRow.java": PROBE_ROW,
        "src/main/java/com/distro/ingest/m7/CoolFold.java": COOL_FOLD,
        "src/main/java/com/distro/ingest/d4/DockParser.java": DOCK_PARSER,
        "src/main/java/com/distro/ingest/d4/DockRow.java": DOCK_ROW,
        "src/main/java/com/distro/ingest/n2/NoticeParser.java": NOTICE_PARSER,
        "src/main/java/com/distro/ingest/n2/NoticeRow.java": NOTICE_ROW,
        "src/main/java/com/distro/ingest/s5/SignoffParser.java": SIGNOFF_PARSER,
        "src/main/java/com/distro/ingest/s5/SignoffRow.java": SIGNOFF_ROW,
        "src/main/java/com/distro/ingest/v6/ReviewParser.java": REVIEW_PARSER,
        "src/main/java/com/distro/ingest/v6/ReviewRow.java": REVIEW_ROW,
        "src/main/java/com/distro/ingest/r3/RouteLoader.java": ROUTE_LOADER,
        "src/main/java/com/distro/ingest/r3/RouteRow.java": ROUTE_ROW,
        "src/main/java/com/distro/engine/p3/PhaseK.java": PHASE_K_BUG,
        "src/main/java/com/distro/engine/p3/RankTable.java": RANK_TABLE,
        "src/main/java/com/distro/engine/p3/ShadowBlend.java": SHADOW_BLEND,
        "src/main/java/com/distro/engine/q1/RulePack.java": RULE_PACK,
        "src/main/java/com/distro/engine/q1/EvalCtx.java": EVAL_CTX,
        "src/main/java/com/distro/model/UnitRef.java": UNIT_REF,
        "src/main/java/com/distro/model/OutRow.java": OUT_ROW,
        "src/main/java/com/distro/model/AuditEntry.java": AUDIT_ENTRY,
        "src/main/java/com/distro/io/JsonWriter.java": JSON_WRITER,
        "src/main/java/com/distro/io/JsonReader.java": JSON_READER,
        "src/main/java/com/distro/io/TsvWriter.java": TSV_WRITER,
        "src/main/java/com/distro/io/CsvReader.java": CSV_READER,
    }
    for rel, body in java_files.items():
        w(f"environment/{rel}", body)

    w("environment/src/main/resources/lab.properties", "lane.prefix=DISTRO\nout.root=/data/out\n")

    w("environment/Dockerfile", DOCKERFILE)
    w("tests/test.sh", TEST_SH)
    w("tests/test_outputs.py", TEST_OUTPUTS)
    w("solution/solve.sh", SOLVE_SH)

    for script in ("environment/scripts/run-cycle.sh", "environment/scripts/build_fixtures.sh"):
        (ROOT / script).chmod(0o755)
    (ROOT / "solution/solve.sh").chmod(0o755)
    (ROOT / "tests/test.sh").chmod(0o755)

    print(f"Generated task at {ROOT}")


FIXTURES_SH = r"""
#!/usr/bin/env bash
set -euo pipefail
BASE=/data/fixtures/days
mkdir -p "$BASE"

write_day() {
  local day="$1"
  local dir="$BASE/$day"
  mkdir -p "$dir"
  case "$day" in
    day_r0412)
      cat >"$dir/notice_feed.csv" <<'CSV'
unit_id,severity,sku_lane
LOT-D742,ACTIVE,DAIRY
CSV
      cat >"$dir/signoff_feed.csv" <<'CSV'
unit_id,auth_id,decision
LOT-D742,SA-9001,GRANT
CSV
      cat >"$dir/review_feed.csv" <<'CSV'
unit_id,status
CSV
      cat >"$dir/probe_feed.csv" <<'CSV'
unit_id,ts_c,probe_c
LOT-D742,100,38
LOT-F881,100,20
CSV
      cat >"$dir/dock_feed.csv" <<'CSV'
unit_id,store_id,qty_cases,parent_id
LOT-D742,ST-11,40,
LOT-F881,ST-22,30,
CSV
      cat >"$dir/route_map.json" <<'JSON'
{"hook_ts":50,"dock_ts":200,"units":["LOT-D742","LOT-F881"]}
JSON
      ;;
    day_r0413)
      cat >"$dir/notice_feed.csv" <<'CSV'
unit_id,severity,sku_lane
CSV
      cat >"$dir/signoff_feed.csv" <<'CSV'
unit_id,auth_id,decision
LOT-K220,SA-9002,GRANT
CSV
      cat >"$dir/review_feed.csv" <<'CSV'
unit_id,status
CSV
      cat >"$dir/probe_feed.csv" <<'CSV'
unit_id,ts_c,probe_c
LOT-K220,30,18
LOT-K220,120,19
CSV
      cat >"$dir/dock_feed.csv" <<'CSV'
unit_id,store_id,qty_cases,parent_id
LOT-K220,ST-33,25,
CSV
      cat >"$dir/route_map.json" <<'JSON'
{"hook_ts":100,"dock_ts":200,"units":["LOT-K220"]}
JSON
      ;;
    day_r0414)
      cat >"$dir/notice_feed.csv" <<'CSV'
unit_id,severity,sku_lane
CSV
      cat >"$dir/signoff_feed.csv" <<'CSV'
unit_id,auth_id,decision
LOT-T119,SA-9003,GRANT
CSV
      cat >"$dir/review_feed.csv" <<'CSV'
unit_id,status
LOT-T119,CLEARED_WITH_SIGNOFF
CSV
      cat >"$dir/probe_feed.csv" <<'CSV'
unit_id,ts_c,probe_c
LOT-T119,40,45
LOT-T119,150,36
CSV
      cat >"$dir/dock_feed.csv" <<'CSV'
unit_id,store_id,qty_cases,parent_id
LOT-T119,ST-44,18,
CSV
      cat >"$dir/route_map.json" <<'JSON'
{"hook_ts":100,"dock_ts":200,"units":["LOT-T119"]}
JSON
      ;;
    day_r0415)
      cat >"$dir/notice_feed.csv" <<'CSV'
unit_id,severity,sku_lane
LOT-P500,ACTIVE,DAIRY
CSV
      cat >"$dir/signoff_feed.csv" <<'CSV'
unit_id,auth_id,decision
CSV
      cat >"$dir/review_feed.csv" <<'CSV'
unit_id,status
CSV
      cat >"$dir/probe_feed.csv" <<'CSV'
unit_id,ts_c,probe_c
LOT-P500A,110,37
LOT-P500B,110,37
CSV
      cat >"$dir/dock_feed.csv" <<'CSV'
unit_id,store_id,qty_cases,parent_id
LOT-P500A,ST-55,10,LOT-P500
LOT-P500B,ST-55,10,LOT-P500
CSV
      cat >"$dir/route_map.json" <<'JSON'
{"hook_ts":100,"dock_ts":200,"units":["LOT-P500A","LOT-P500B"]}
JSON
      ;;
    day_r0416)
      cat >"$dir/notice_feed.csv" <<'CSV'
unit_id,severity,sku_lane
LOT-H901,ACTIVE,DAIRY
CSV
      cat >"$dir/signoff_feed.csv" <<'CSV'
unit_id,auth_id,decision
LOT-H901,SA-9010,GRANT
CSV
      cat >"$dir/review_feed.csv" <<'CSV'
unit_id,status
CSV
      cat >"$dir/probe_feed.csv" <<'CSV'
unit_id,ts_c,probe_c
LOT-H901,120,39
CSV
      cat >"$dir/dock_feed.csv" <<'CSV'
unit_id,store_id,qty_cases,parent_id
LOT-H901,ST-66,12,
LOT-H901,ST-77,8,
CSV
      cat >"$dir/route_map.json" <<'JSON'
{"hook_ts":100,"dock_ts":200,"units":["LOT-H901"]}
JSON
      ;;
  esac
}

for d in day_r0412 day_r0413 day_r0414 day_r0415 day_r0416; do
  write_day "$d"
done
"""

APP_JAVA = """
package com.distro;

public final class App {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: App <day> <root>");
            System.exit(2);
        }
        new CycleCmd().run(args[0], args[1]);
    }
}
"""

CYCLE_CMD_JAVA = """
package com.distro;

import com.distro.core.r8.Orchestrator;

public final class CycleCmd {
    public void run(String day, String root) throws Exception {
        Orchestrator orchestrator = new Orchestrator();
        orchestrator.execute(day, root);
    }
}
"""

PROPS_LOADER = """
package com.distro.cfg;

import java.io.InputStream;
import java.util.Properties;

public final class PropsLoader {
    public LaneCfg load() throws Exception {
        Properties p = new Properties();
        try (InputStream in = PropsLoader.class.getResourceAsStream("/lab.properties")) {
            if (in != null) {
                p.load(in);
            }
        }
        return new LaneCfg(p.getProperty("lane.prefix", "DISTRO"), p.getProperty("out.root", "/data/out"));
    }
}
"""

LANE_CFG = """
package com.distro.cfg;

public record LaneCfg(String prefix, String outRoot) {}
"""

STEP2_BUG = """
package com.distro.core.k9;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public final class Step2 {
    public static List<String> resolve_d(String p, Map<String, List<String>> m) {
        List<String> kids = m.get(p);
        if (kids == null || kids.isEmpty()) {
            return List.of(p);
        }
        return List.of(kids.get(0));
    }

    public static List<String> expandAll(String p, Map<String, List<String>> m) {
        return new ArrayList<>(resolve_d(p, m));
    }
}
"""

UNIT_GRAPH = """
package com.distro.core.k9;

import com.distro.ingest.d4.DockRow;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class UnitGraph {
    public Map<String, List<String>> splitsFromDock(List<DockRow> dockRows) {
        Map<String, List<String>> out = new HashMap<>();
        for (DockRow row : dockRows) {
            if (row.parentId() != null && !row.parentId().isBlank()) {
                out.computeIfAbsent(row.parentId(), k -> new ArrayList<>()).add(row.unitId());
            }
        }
        return out;
    }
}
"""

LEGACY_BIND = """
package com.distro.core.k9;

import java.util.HashMap;
import java.util.Map;

public final class LegacyBind {
    public Map<String, String> resolve_d(String legacyId) {
        Map<String, String> m = new HashMap<>();
        m.put(legacyId, "WH-" + legacyId);
        return m;
    }
}
"""

ORCHESTRATOR = """
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
        List<ProbeRow> probes = ScanC.read(dayDir.resolve("probe_feed.csv"));
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
                audit.add(new AuditEntry(unit, signoff.authId(), signoff.decision(), PhaseK.rank(signoff, notice)));
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
"""

BATCH_CTX = """
package com.distro.core.r8;

public final class BatchCtx {
    private final String day;
    private final String root;

    public BatchCtx(String day, String root) {
        this.day = day;
        this.root = root;
    }

    public String day() { return day; }
    public String root() { return root; }
}
"""

STAGE_GATE = """
package com.distro.core.r8;

public final class StageGate {
    public boolean allow(String phase) {
        return !"legacy".equals(phase);
    }
}
"""

SCAN_C_BUG = """
package com.distro.ingest.m7;

import com.distro.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class ScanC {
    public static List<ProbeRow> read(Path path) throws Exception {
        List<ProbeRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new ProbeRow(cols[0], Long.parseLong(cols[1]), Integer.parseInt(cols[2])));
        }
        return rows;
    }

    public static List<ProbeRow> fold_a(List<ProbeRow> rows, long x, long y) {
        List<ProbeRow> out = new ArrayList<>();
        for (ProbeRow r : rows) {
            if (r.ts() >= x + 50 && r.ts() <= y) {
                out.add(r);
            }
        }
        return out;
    }
}
"""

PROBE_ROW = """
package com.distro.ingest.m7;

public record ProbeRow(String unitId, long ts, int probeC) {}
"""

COOL_FOLD = """
package com.distro.ingest.m7;

import java.util.ArrayList;
import java.util.List;

public final class CoolFold {
    public static double fold_a(List<Integer> samples) {
        if (samples.isEmpty()) {
            return 0.0;
        }
        int sum = 0;
        for (int v : samples) {
            sum += v;
        }
        return sum / (double) samples.size();
    }

    public static List<Integer> window(List<Integer> all, int start, int end) {
        List<Integer> out = new ArrayList<>();
        for (int i = start; i < end && i < all.size(); i++) {
            out.add(all.get(i));
        }
        return out;
    }
}
"""

DOCK_PARSER = """
package com.distro.ingest.d4;

import com.distro.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class DockParser {
    public List<DockRow> read(Path path) throws Exception {
        List<DockRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            String parent = cols.length > 3 && !cols[3].isBlank() ? cols[3] : null;
            rows.add(new DockRow(cols[0], cols[1], Integer.parseInt(cols[2]), parent));
        }
        return rows;
    }
}
"""

DOCK_ROW = """
package com.distro.ingest.d4;

public record DockRow(String unitId, String storeId, int qtyCases, String parentId) {}
"""

NOTICE_PARSER = """
package com.distro.ingest.n2;

import com.distro.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class NoticeParser {
    public List<NoticeRow> read(Path path) throws Exception {
        List<NoticeRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new NoticeRow(cols[0], cols[1], cols[2]));
        }
        return rows;
    }
}
"""

NOTICE_ROW = """
package com.distro.ingest.n2;

public record NoticeRow(String unitId, String severity, String skuLane) {}
"""

SIGNOFF_PARSER = """
package com.distro.ingest.s5;

import com.distro.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class SignoffParser {
    public List<SignoffRow> read(Path path) throws Exception {
        List<SignoffRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new SignoffRow(cols[0], cols[1], cols[2]));
        }
        return rows;
    }
}
"""

SIGNOFF_ROW = """
package com.distro.ingest.s5;

public record SignoffRow(String unitId, String authId, String decision) {}
"""

REVIEW_PARSER = """
package com.distro.ingest.v6;

import com.distro.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class ReviewParser {
    public List<ReviewRow> read(Path path) throws Exception {
        List<ReviewRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new ReviewRow(cols[0], cols[1]));
        }
        return rows;
    }
}
"""

REVIEW_ROW = """
package com.distro.ingest.v6;

public record ReviewRow(String unitId, String status) {}
"""

ROUTE_LOADER = """
package com.distro.ingest.r3;

import com.distro.io.JsonReader;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public final class RouteLoader {
    public record RouteMeta(long hookTs, long dockTs, List<String> units) {}

    public RouteMeta read(Path path) throws Exception {
        Map<String, Object> m = JsonReader.readObject(path);
        long hook = ((Number) m.get("hook_ts")).longValue();
        long dock = ((Number) m.get("dock_ts")).longValue();
        @SuppressWarnings("unchecked")
        List<String> units = (List<String>) m.get("units");
        return new RouteMeta(hook, dock, units);
    }
}
"""

ROUTE_ROW = """
package com.distro.ingest.r3;

public record RouteRow(String unitId, String routeCode) {}
"""

PHASE_K_BUG = """
package com.distro.engine.p3;

import com.distro.ingest.n2.NoticeRow;
import com.distro.ingest.s5.SignoffRow;
import com.distro.ingest.v6.ReviewRow;

public final class PhaseK {
    public static String merge_b(NoticeRow a, SignoffRow b, ReviewRow c) {
        if (b != null && "GRANT".equals(b.decision())) {
            return "RELEASED";
        }
        if (a != null && "ACTIVE".equals(a.severity())) {
            return "HELD";
        }
        if (c != null && "CLEARED_WITH_SIGNOFF".equals(c.status())) {
            return "HELD";
        }
        return "RELEASED";
    }

    public static int rank(SignoffRow b, NoticeRow a) {
        if (a != null && "ACTIVE".equals(a.severity())) {
            return 1;
        }
        return b == null ? 99 : 5;
    }
}
"""

RANK_TABLE = """
package com.distro.engine.p3;

public final class RankTable {
    public static int base(String lane) {
        return switch (lane) {
            case "DAIRY" -> 2;
            case "FROZEN" -> 4;
            default -> 10;
        };
    }
}
"""

SHADOW_BLEND = """
package com.distro.engine.p3;

import com.distro.ingest.r3.RouteRow;
import java.util.List;

public final class ShadowBlend {
    public static String merge_b(List<RouteRow> rows) {
        if (rows.isEmpty()) {
            return "NONE";
        }
        return rows.get(0).routeCode();
    }
}
"""

RULE_PACK = """
package com.distro.engine.q1;

import com.distro.ingest.n2.NoticeRow;
import com.distro.ingest.v6.ReviewRow;

public final class RulePack {
    public static String reason(EvalCtx ctx) {
        if ("HELD".equals(ctx.state())) {
            if (ctx.notice() != null && "ACTIVE".equals(ctx.notice().severity())) {
                return "NOTICE_ACTIVE";
            }
            if (!ctx.inProbeWindow()) {
                return "PROBE_GAP";
            }
            if (ctx.review() != null && !"CLEARED_WITH_SIGNOFF".equals(ctx.review().status())) {
                return "REVIEW_OPEN";
            }
            return "POLICY_HOLD";
        }
        return "OK_RELEASE";
    }
}
"""

EVAL_CTX = """
package com.distro.engine.q1;

import com.distro.ingest.n2.NoticeRow;
import com.distro.ingest.v6.ReviewRow;

public record EvalCtx(String state, NoticeRow notice, ReviewRow review, boolean inProbeWindow) {}
"""

UNIT_REF = """
package com.distro.model;

public record UnitRef(String id, String lane) {}
"""

OUT_ROW = """
package com.distro.model;

public record OutRow(String unitId, String stateOrStore, String reasonOrClass, int qtyOrDay) {}
"""

AUDIT_ENTRY = """
package com.distro.model;

public record AuditEntry(String unitId, String authId, String decision, int precedenceRank) {}
"""

JSON_WRITER = """
package com.distro.io;

import com.distro.model.AuditEntry;
import com.distro.model.OutRow;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

public final class JsonWriter {
    public void writeLedger(Path path, List<OutRow> rows) throws Exception {
        StringBuilder sb = new StringBuilder();
        for (OutRow r : rows) {
            sb.append(String.format(
                "{\"unit_id\":\"%s\",\"state\":\"%s\",\"reason_code\":\"%s\",\"source_day\":%d}%n",
                r.unitId(), r.stateOrStore(), r.reasonOrClass(), r.qtyOrDay()));
        }
        Files.writeString(path, sb.toString());
    }

    public void writeAudit(Path path, List<AuditEntry> entries) throws Exception {
        StringBuilder sb = new StringBuilder();
        sb.append("{\"version\":1,\"entries\":[");
        for (int i = 0; i < entries.size(); i++) {
            AuditEntry e = entries.get(i);
            if (i > 0) sb.append(',');
            sb.append(String.format(
                "{\"unit_id\":\"%s\",\"auth_id\":\"%s\",\"decision\":\"%s\",\"precedence_rank\":%d}",
                e.unitId(), e.authId(), e.decision(), e.precedenceRank()));
        }
        sb.append("]}");
        Files.writeString(path, sb.toString());
    }
}
"""

JSON_READER = """
package com.distro.io;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class JsonReader {
    public static Map<String, Object> readObject(Path path) throws Exception {
        String raw = Files.readString(path).trim();
        Map<String, Object> out = new HashMap<>();
        Matcher hook = Pattern.compile("\\\"hook_ts\\\"\\\\s*:\\\\s*(\\\\d+)").matcher(raw);
        Matcher dock = Pattern.compile("\\\"dock_ts\\\"\\\\s*:\\\\s*(\\\\d+)").matcher(raw);
        if (hook.find()) {
            out.put("hook_ts", Long.parseLong(hook.group(1)));
        }
        if (dock.find()) {
            out.put("dock_ts", Long.parseLong(dock.group(1)));
        }
        List<String> units = new ArrayList<>();
        Matcher unit = Pattern.compile("\\\"(LOT-[A-Z0-9]+)\\\"").matcher(raw);
        while (unit.find()) {
            units.add(unit.group(1));
        }
        out.put("units", units);
        return out;
    }
}
"""

TSV_WRITER = """
package com.distro.io;

import com.distro.model.OutRow;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public final class TsvWriter {
    public void write(Path path, List<OutRow> rows) throws Exception {
        List<OutRow> sorted = new ArrayList<>(rows);
        sorted.sort(Comparator.comparing(OutRow::unitId));
        List<String> lines = new ArrayList<>();
        lines.add("unit_id\\tstore_id\\texposure_class\\tqty_cases");
        for (OutRow r : sorted) {
            lines.add(String.format("%s\\t%s\\t%s\\t%d", r.unitId(), r.stateOrStore(), r.reasonOrClass(), r.qtyOrDay()));
        }
        Files.write(path, lines);
    }
}
"""

CSV_READER = """
package com.distro.io;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class CsvReader {
    public static List<String[]> read(Path path) throws Exception {
        List<String[]> rows = new ArrayList<>();
        List<String> lines = Files.readAllLines(path);
        boolean first = true;
        for (String line : lines) {
            if (line.isBlank()) continue;
            if (first) { first = false; continue; }
            rows.add(line.split(",", -1));
        }
        return rows;
    }
}
"""

DOCKERFILE = """
# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build
COPY pom.xml .
COPY src ./src
COPY config ./config
RUN mvn -q package

FROM public.ecr.aws/docker/library/eclipse-temurin:17-jre-jammy

RUN apt-get update \
    && apt-get install -y --no-install-recommends \\
        asciinema \\
        tmux \\
        python3 \\
        python3-pip \\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

COPY --from=builder /build/target/cycle-batch-1.0.0.jar /opt/distro/target/cycle-batch-1.0.0.jar
COPY pom.xml /opt/distro/pom.xml
COPY src /opt/distro/src
COPY config /opt/distro/config
COPY scripts /opt/distro/scripts/
COPY --from=builder /build/target /opt/distro/target

RUN chmod +x /opt/distro/scripts/*.sh \\
    && /opt/distro/scripts/build_fixtures.sh

WORKDIR /opt/distro
"""

TEST_SH = """
#!/bin/bash

mkdir -p /logs/verifier

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set." >&2
    echo 0 > /logs/verifier/reward.txt
    exit 1
fi

python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
  --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
"""

TEST_OUTPUTS = '''
"""Verifier tests for food recall cold-chain holdback outcomes."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path("/data/fixtures")
OUT = Path("/data/out")
RUN = ["/opt/distro/scripts/run-cycle.sh"]


def _run(day: str) -> None:
    out_dir = OUT / day
    if out_dir.exists():
        for p in out_dir.iterdir():
            p.unlink()
    subprocess.check_call(RUN + ["--day", day, "--root", str(ROOT)])


def _ledger(day: str) -> list[dict]:
    rows = []
    for line in (OUT / day / "holdback_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _state(day: str, unit: str) -> str:
    for row in _ledger(day):
        if row["unit_id"] == unit:
            return row["state"]
    raise AssertionError(f"missing unit {unit} on {day}")


def test_k9_active_notice_blocks():
    """Recalled dairy unit stays HELD despite signoff grant."""
    _run("day_r0412")
    assert _state("day_r0412", "LOT-D742") == "HELD"
    assert _state("day_r0412", "LOT-F881") == "RELEASED"


def test_m4_unrelated_release():
    """Unrelated frozen unit releases when probe window is valid."""
    _run("day_r0413")
    assert _state("day_r0413", "LOT-K220") == "RELEASED"


def test_p2_cleared_excursion():
    """Cleared review with signoff releases held excursion case."""
    _run("day_r0414")
    assert _state("day_r0414", "LOT-T119") == "RELEASED"


def test_q7_split_lineage():
    """Both dock-split children stay HELD when parent flagged."""
    _run("day_r0415")
    assert _state("day_r0415", "LOT-P500A") == "HELD"
    assert _state("day_r0415", "LOT-P500B") == "HELD"


def test_s3_rerun_stable():
    """Two consecutive runs produce identical ledger and TSV bytes."""
    _run("day_r0415")
    ledger_a = (OUT / "day_r0415" / "holdback_ledger.jsonl").read_bytes()
    tsv_a = (OUT / "day_r0415" / "affected_units.tsv").read_bytes()
    _run("day_r0415")
    ledger_b = (OUT / "day_r0415" / "holdback_ledger.jsonl").read_bytes()
    tsv_b = (OUT / "day_r0415" / "affected_units.tsv").read_bytes()
    assert hashlib.sha256(ledger_a).hexdigest() == hashlib.sha256(ledger_b).hexdigest()
    assert hashlib.sha256(tsv_a).hexdigest() == hashlib.sha256(tsv_b).hexdigest()


def test_w2_hidden_day():
    """Hidden distribution day blocks cross-store recalled unit."""
    _run("day_r0416")
    assert _state("day_r0416", "LOT-H901") == "HELD"
    tsv = (OUT / "day_r0416" / "affected_units.tsv").read_text(encoding="utf-8")
    assert "ST-66" in tsv
    assert "ST-77" in tsv
'''

SOLVE_SH = r"""
#!/usr/bin/env bash
set -euo pipefail

cd /opt/distro

python3 <<'PY'
from pathlib import Path

root = Path("src/main/java/com/distro")

phase = root / "engine/p3/PhaseK.java"
text = phase.read_text(encoding="utf-8")
old = '''    public static String merge_b(NoticeRow a, SignoffRow b, ReviewRow c) {
        if (c != null && "CLEARED_WITH_SIGNOFF".equals(c.status())) {
            return "HELD";
        }
        if (b != null && "GRANT".equals(b.decision())) {
            return "RELEASED";
        }
        if (a != null && "ACTIVE".equals(a.severity())) {
            return "HELD";
        }
        return "RELEASED";
    }'''
new = '''    public static String merge_b(NoticeRow a, SignoffRow b, ReviewRow c) {
        if (a != null && "ACTIVE".equals(a.severity())) {
            if (c != null && "CLEARED_WITH_SIGNOFF".equals(c.status())
                && b != null && "GRANT".equals(b.decision())) {
                return "RELEASED";
            }
            return "HELD";
        }
        if (b != null && "GRANT".equals(b.decision())) {
            return "RELEASED";
        }
        if (c != null && "CLEARED_WITH_SIGNOFF".equals(c.status())) {
            return "RELEASED";
        }
        return "RELEASED";
    }'''
if old not in text:
    raise SystemExit("PhaseK pattern missing")
phase.write_text(text.replace(old, new), encoding="utf-8")

scan = root / "ingest/m7/ScanC.java"
text = scan.read_text(encoding="utf-8")
old = '''            if (r.ts() >= x + 50 && r.ts() <= y) {
                out.add(r);
            }'''
new = '''            if (r.ts() >= x && r.ts() <= y) {
                out.add(r);
            }'''
if old not in text:
    raise SystemExit("ScanC pattern missing")
scan.write_text(text.replace(old, new), encoding="utf-8")

step = root / "core/k9/Step2.java"
text = step.read_text(encoding="utf-8")
old = '''        return List.of(kids.get(0));'''
new = '''        return new java.util.ArrayList<>(kids);'''
if old not in text:
    raise SystemExit("Step2 pattern missing")
step.write_text(text.replace(old, new), encoding="utf-8")
PY

mvn -q package
cp target/cycle-batch-1.0.0.jar /opt/distro/target/cycle-batch-1.0.0.jar

for day in day_r0412 day_r0413 day_r0414 day_r0415 day_r0416; do
  /opt/distro/scripts/run-cycle.sh --day "$day" --root /data/fixtures
done
"""

if __name__ == "__main__":
    main()
