#!/usr/bin/env python3
"""Generate rare-book-quarantine-circulation task files."""
from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "rare-book-quarantine-circulation"
ENV = ROOT / "environment"


def w(rel: str, content: str) -> None:
    p = ROOT / rel if not rel.startswith("environment/") else ENV / rel.removeprefix("environment/")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def main() -> None:
    w(
        "instruction.md",
        """
        The national archives circulation desk runs a Java batch job from `/opt/archives/scripts/run-cycle.sh`
        with `--day <collection-day>` and `--root /data/fixtures`. It ingests quarantine feeds, covenant
        feeds, exhibit feeds, RFID feeds, circulation feeds, and sweep maps, then writes
        `/data/out/<day>/loan_decision_ledger.jsonl` (volume_id, decision, reason_code, collection_day),
        `/data/out/<day>/quarantine_exceptions.json` (version, entries), and
        `/data/out/<day>/shelf_custody_audit.tsv` (volume_id, branch_id, custody_class, request_qty).

        Conservation policy refresh regressed the circulation batch. Active quarantine should deny loans even when a donor
        covenant grants release; flagged volumes currently read loanable on those days. Unrelated reading-room units should
        loan when their RFID sweep is in window; they currently read blocked. Cleared exhibit paperwork should open the
        case; those sweeps currently read locked. Flagged parents should hold every bound sibling; siblings currently read
        circulating. Identical collection-day reruns should produce stable shelf-custody audit bytes. A volume denied at
        multiple branches needs one audit row per branch, not one row per volume.

        Rebuild the Maven project under `/opt/archives`, rerun the cycle for every collection day present
        under `/data/fixtures`, and leave those fixtures unchanged. Conservation auditors first spotted
        symptoms on `day_c0901` through `day_c0905`.
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
        category = "data-processing"
        subcategories = []
        number_of_milestones = 0
        codebase_size = "small"
        languages = ["java", "bash"]
        tags = ["java", "library", "heritage", "circulation", "conservation", "batch"]
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
          "/data/out/<day>/loan_decision_ledger.jsonl",
          "/data/out/<day>/quarantine_exceptions.json",
          "/data/out/<day>/shelf_custody_audit.tsv",
        ]

        internal_harness_files = [
          "/data/fixtures/days/",
        ]

        [structured_outputs.loan_decision_ledger]
        target = "/data/out/<day>/loan_decision_ledger.jsonl"
        format = "jsonl"
        instruction_checks = ["volume_id", "decision", "reason_code", "collection_day"]

        [structured_outputs.quarantine_exceptions]
        target = "/data/out/<day>/quarantine_exceptions.json"
        format = "json"
        instruction_checks = ["version", "entries"]

        [structured_outputs.shelf_custody_audit]
        target = "/data/out/<day>/shelf_custody_audit.tsv"
        format = "tsv"
        instruction_checks = ["volume_id", "branch_id", "custody_class", "request_qty"]
        """,
    )

    w(
        "environment/.dockerignore",
        """
        .git
        .gitignore
        **/__pycache__/
        **/*.pyc
        **/.pytest_cache/
        **/.mypy_cache/
        **/.ruff_cache/
        **/node_modules/
        **/target/
        **/dist/
        **/build/
        **/.venv/
        **/venv/
        .env
        *.log
        solution/
        tests/
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
          <groupId>com.archives</groupId>
          <artifactId>circulation-batch</artifactId>
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
                      <mainClass>com.archives.App</mainClass>
                    </manifest>
                  </archive>
                </configuration>
              </plugin>
            </plugins>
          </build>
        </project>
        """,
    )

    w("environment/config/lab.properties", "lane.prefix=ARCHIVE\nout.root=/data/out\n")

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
        java -jar /opt/archives/target/circulation-batch-1.0.0.jar "$DAY" "$ROOT"
        """,
    )

    w(
        "environment/scripts/build_fixtures.sh",
        FIXTURES_SH,
    )

    java_files = {
        "src/main/java/com/archives/App.java": APP_JAVA,
        "src/main/java/com/archives/CycleCmd.java": CYCLE_CMD_JAVA,
        "src/main/java/com/archives/cfg/PropsLoader.java": PROPS_LOADER,
        "src/main/java/com/archives/cfg/LaneCfg.java": LANE_CFG,
        "src/main/java/com/archives/core/k9/LineageExpand.java": LINEAGE_EXPAND_BUG,
        "src/main/java/com/archives/core/k9/VolumeGraph.java": UNIT_GRAPH,
        "src/main/java/com/archives/core/k9/LegacyBind.java": LEGACY_BIND,
        "src/main/java/com/archives/core/r8/Orchestrator.java": ORCHESTRATOR,
        "src/main/java/com/archives/core/r8/BatchCtx.java": BATCH_CTX,
        "src/main/java/com/archives/core/r8/StageGate.java": STAGE_GATE,
        "src/main/java/com/archives/ingest/m7/RfidFold.java": RFID_FOLD_BUG,
        "src/main/java/com/archives/ingest/m7/RfidRow.java": PROBE_ROW,
        "src/main/java/com/archives/ingest/m7/SignalFold.java": COOL_FOLD,
        "src/main/java/com/archives/ingest/d4/CirculationParser.java": DOCK_PARSER,
        "src/main/java/com/archives/ingest/d4/CirculationRow.java": DOCK_ROW,
        "src/main/java/com/archives/ingest/n2/QuarantineParser.java": NOTICE_PARSER,
        "src/main/java/com/archives/ingest/n2/QuarantineRow.java": NOTICE_ROW,
        "src/main/java/com/archives/ingest/s5/CovenantParser.java": SIGNOFF_PARSER,
        "src/main/java/com/archives/ingest/s5/CovenantRow.java": SIGNOFF_ROW,
        "src/main/java/com/archives/ingest/v6/ExhibitParser.java": REVIEW_PARSER,
        "src/main/java/com/archives/ingest/v6/ExhibitRow.java": REVIEW_ROW,
        "src/main/java/com/archives/ingest/r3/SweepLoader.java": ROUTE_LOADER,
        "src/main/java/com/archives/ingest/r3/SweepRow.java": ROUTE_ROW,
        "src/main/java/com/archives/engine/p3/MergeLane.java": MERGE_LANE_BUG,
        "src/main/java/com/archives/engine/p3/RankTable.java": RANK_TABLE,
        "src/main/java/com/archives/engine/p3/ShadowBlend.java": SHADOW_BLEND,
        "src/main/java/com/archives/engine/q1/RulePack.java": RULE_PACK,
        "src/main/java/com/archives/engine/q1/EvalCtx.java": EVAL_CTX,
        "src/main/java/com/archives/model/VolumeRef.java": UNIT_REF,
        "src/main/java/com/archives/model/OutRow.java": OUT_ROW,
        "src/main/java/com/archives/model/AuditEntry.java": AUDIT_ENTRY,
        "src/main/java/com/archives/io/JsonWriter.java": JSON_WRITER,
        "src/main/java/com/archives/io/JsonReader.java": JSON_READER,
        "src/main/java/com/archives/io/TsvWriter.java": TSV_WRITER_BUG,
        "src/main/java/com/archives/io/CsvReader.java": CSV_READER,
    }
    for rel, body in java_files.items():
        w(f"environment/{rel}", body)

    w("environment/src/main/resources/lab.properties", "lane.prefix=ARCHIVE\nout.root=/data/out\n")

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
    day_c0901)
      cat >"$dir/quarantine_feed.csv" <<'CSV'
volume_id,severity,collection_lane
VOL-D742,ACTIVE,RARE
CSV
      cat >"$dir/covenant_feed.csv" <<'CSV'
volume_id,auth_id,decision
VOL-D742,SA-9001,GRANT
CSV
      cat >"$dir/exhibit_feed.csv" <<'CSV'
volume_id,status
CSV
      cat >"$dir/rfid_feed.csv" <<'CSV'
volume_id,ts,signal_strength
VOL-D742,100,38
VOL-F881,100,20
CSV
      cat >"$dir/circulation_feed.csv" <<'CSV'
volume_id,branch_id,request_qty,parent_id
VOL-D742,ST-11,40,
VOL-F881,ST-22,30,
CSV
      cat >"$dir/sweep_map.json" <<'JSON'
{"sweep_start_ts":50,"sweep_end_ts":200,"units":["VOL-D742","VOL-F881"]}
JSON
      ;;
    day_c0902)
      cat >"$dir/quarantine_feed.csv" <<'CSV'
volume_id,severity,collection_lane
CSV
      cat >"$dir/covenant_feed.csv" <<'CSV'
volume_id,auth_id,decision
VOL-K220,SA-9002,GRANT
CSV
      cat >"$dir/exhibit_feed.csv" <<'CSV'
volume_id,status
CSV
      cat >"$dir/rfid_feed.csv" <<'CSV'
volume_id,ts,signal_strength
VOL-K220,30,18
VOL-K220,120,19
CSV
      cat >"$dir/circulation_feed.csv" <<'CSV'
volume_id,branch_id,request_qty,parent_id
VOL-K220,ST-33,25,
CSV
      cat >"$dir/sweep_map.json" <<'JSON'
{"sweep_start_ts":100,"sweep_end_ts":200,"units":["VOL-K220"]}
JSON
      ;;
    day_c0903)
      cat >"$dir/quarantine_feed.csv" <<'CSV'
volume_id,severity,collection_lane
CSV
      cat >"$dir/covenant_feed.csv" <<'CSV'
volume_id,auth_id,decision
VOL-T119,SA-9003,GRANT
CSV
      cat >"$dir/exhibit_feed.csv" <<'CSV'
volume_id,status
VOL-T119,CLEARED_FOR_EXHIBIT
CSV
      cat >"$dir/rfid_feed.csv" <<'CSV'
volume_id,ts,signal_strength
VOL-T119,40,45
VOL-T119,150,36
CSV
      cat >"$dir/circulation_feed.csv" <<'CSV'
volume_id,branch_id,request_qty,parent_id
VOL-T119,ST-44,18,
CSV
      cat >"$dir/sweep_map.json" <<'JSON'
{"sweep_start_ts":100,"sweep_end_ts":200,"units":["VOL-T119"]}
JSON
      ;;
    day_c0904)
      cat >"$dir/quarantine_feed.csv" <<'CSV'
volume_id,severity,collection_lane
VOL-P500,ACTIVE,RARE
CSV
      cat >"$dir/covenant_feed.csv" <<'CSV'
volume_id,auth_id,decision
CSV
      cat >"$dir/exhibit_feed.csv" <<'CSV'
volume_id,status
CSV
      cat >"$dir/rfid_feed.csv" <<'CSV'
volume_id,ts,signal_strength
VOL-P500A,110,37
VOL-P500B,110,37
CSV
      cat >"$dir/circulation_feed.csv" <<'CSV'
volume_id,branch_id,request_qty,parent_id
VOL-P500A,ST-55,10,VOL-P500
VOL-P500B,ST-55,10,VOL-P500
CSV
      cat >"$dir/sweep_map.json" <<'JSON'
{"sweep_start_ts":100,"sweep_end_ts":200,"units":["VOL-P500A","VOL-P500B"]}
JSON
      ;;
    day_c0906)
      cat >"$dir/quarantine_feed.csv" <<'CSV'
volume_id,severity,collection_lane
VOL-H901,ACTIVE,RARE
CSV
      cat >"$dir/covenant_feed.csv" <<'CSV'
volume_id,auth_id,decision
VOL-H901,SA-9010,GRANT
CSV
      cat >"$dir/exhibit_feed.csv" <<'CSV'
volume_id,status
CSV
      cat >"$dir/rfid_feed.csv" <<'CSV'
volume_id,ts,signal_strength
VOL-H901,120,39
CSV
      cat >"$dir/circulation_feed.csv" <<'CSV'
volume_id,branch_id,request_qty,parent_id
VOL-H901,ST-66,12,
VOL-H901,ST-77,8,
CSV
      cat >"$dir/sweep_map.json" <<'JSON'
{"sweep_start_ts":100,"sweep_end_ts":200,"units":["VOL-H901"]}
JSON
      ;;
  esac
}

for d in day_c0901 day_c0902 day_c0903 day_c0904 day_c0906; do
  write_day "$d"
done
"""

APP_JAVA = """
package com.archives;

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
package com.archives;

import com.archives.core.r8.Orchestrator;

public final class CycleCmd {
    public void run(String day, String root) throws Exception {
        Orchestrator orchestrator = new Orchestrator();
        orchestrator.execute(day, root);
    }
}
"""

PROPS_LOADER = """
package com.archives.cfg;

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
        return new LaneCfg(p.getProperty("lane.prefix", "ARCHIVE"), p.getProperty("out.root", "/data/out"));
    }
}
"""

LANE_CFG = """
package com.archives.cfg;

public record LaneCfg(String prefix, String outRoot) {}
"""

LINEAGE_EXPAND_BUG = """
package com.archives.core.k9;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public final class LineageExpand {
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
package com.archives.core.k9;

import com.archives.ingest.d4.CirculationRow;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class VolumeGraph {
    public Map<String, List<String>> splitsFromCirculation(List<CirculationRow> dockRows) {
        Map<String, List<String>> out = new HashMap<>();
        for (CirculationRow row : dockRows) {
            if (row.parentId() != null && !row.parentId().isBlank()) {
                out.computeIfAbsent(row.parentId(), k -> new ArrayList<>()).add(row.unitId());
            }
        }
        return out;
    }
}
"""

LEGACY_BIND = """
package com.archives.core.k9;

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
"""

BATCH_CTX = """
package com.archives.core.r8;

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
package com.archives.core.r8;

public final class StageGate {
    public boolean allow(String phase) {
        return !"legacy".equals(phase);
    }
}
"""

RFID_FOLD_BUG = """
package com.archives.ingest.m7;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class RfidFold {
    public static List<RfidRow> read(Path path) throws Exception {
        List<RfidRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new RfidRow(cols[0], Long.parseLong(cols[1]), Integer.parseInt(cols[2])));
        }
        return rows;
    }

    public static List<RfidRow> fold_a(List<RfidRow> rows, long x, long y) {
        List<RfidRow> out = new ArrayList<>();
        for (RfidRow r : rows) {
            if (r.ts() >= x + 50 && r.ts() <= y) {
                out.add(r);
            }
        }
        return out;
    }
}
"""

PROBE_ROW = """
package com.archives.ingest.m7;

public record RfidRow(String unitId, long ts, int probeC) {}
"""

COOL_FOLD = """
package com.archives.ingest.m7;

import java.util.ArrayList;
import java.util.List;

public final class SignalFold {
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
package com.archives.ingest.d4;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class CirculationParser {
    public List<CirculationRow> read(Path path) throws Exception {
        List<CirculationRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            String parent = cols.length > 3 && !cols[3].isBlank() ? cols[3] : null;
            rows.add(new CirculationRow(cols[0], cols[1], Integer.parseInt(cols[2]), parent));
        }
        return rows;
    }
}
"""

DOCK_ROW = """
package com.archives.ingest.d4;

public record CirculationRow(String unitId, String storeId, int qtyCases, String parentId) {}
"""

NOTICE_PARSER = """
package com.archives.ingest.n2;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class QuarantineParser {
    public List<QuarantineRow> read(Path path) throws Exception {
        List<QuarantineRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new QuarantineRow(cols[0], cols[1], cols[2]));
        }
        return rows;
    }
}
"""

NOTICE_ROW = """
package com.archives.ingest.n2;

public record QuarantineRow(String unitId, String severity, String skuLane) {}
"""

SIGNOFF_PARSER = """
package com.archives.ingest.s5;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class CovenantParser {
    public List<CovenantRow> read(Path path) throws Exception {
        List<CovenantRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new CovenantRow(cols[0], cols[1], cols[2]));
        }
        return rows;
    }
}
"""

SIGNOFF_ROW = """
package com.archives.ingest.s5;

public record CovenantRow(String unitId, String authId, String decision) {}
"""

REVIEW_PARSER = """
package com.archives.ingest.v6;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class ExhibitParser {
    public List<ExhibitRow> read(Path path) throws Exception {
        List<ExhibitRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new ExhibitRow(cols[0], cols[1]));
        }
        return rows;
    }
}
"""

REVIEW_ROW = """
package com.archives.ingest.v6;

public record ExhibitRow(String unitId, String status) {}
"""

ROUTE_LOADER = """
package com.archives.ingest.r3;

import com.archives.io.JsonReader;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public final class SweepLoader {
    public record SweepMeta(long hookTs, long dockTs, List<String> units) {}

    public SweepMeta read(Path path) throws Exception {
        Map<String, Object> m = JsonReader.readObject(path);
        long hook = ((Number) m.get("sweep_start_ts")).longValue();
        long dock = ((Number) m.get("sweep_end_ts")).longValue();
        @SuppressWarnings("unchecked")
        List<String> units = (List<String>) m.get("units");
        return new SweepMeta(hook, dock, units);
    }
}
"""

ROUTE_ROW = """
package com.archives.ingest.r3;

public record SweepRow(String unitId, String routeCode) {}
"""

MERGE_LANE_BUG = """
package com.archives.engine.p3;

import com.archives.ingest.n2.QuarantineRow;
import com.archives.ingest.s5.CovenantRow;
import com.archives.ingest.v6.ExhibitRow;

public final class MergeLane {
    public static String merge_b(QuarantineRow a, CovenantRow b, ExhibitRow c) {
        if (b != null && "GRANT".equals(b.decision())) {
            return "ALLOW";
        }
        if (a != null && "ACTIVE".equals(a.severity())) {
            return "DENIED_LOAN";
        }
        if (c != null && "CLEARED_FOR_EXHIBIT".equals(c.status())) {
            return "DENIED_LOAN";
        }
        return "ALLOW";
    }

    public static int rank(CovenantRow b, QuarantineRow a) {
        if (a != null && "ACTIVE".equals(a.severity())) {
            return 1;
        }
        return b == null ? 99 : 5;
    }
}
"""

RANK_TABLE = """
package com.archives.engine.p3;

public final class RankTable {
    public static int base(String lane) {
        return switch (lane) {
            case "RARE" -> 2;
            case "GENERAL" -> 4;
            default -> 10;
        };
    }
}
"""

SHADOW_BLEND = """
package com.archives.engine.p3;

import com.archives.ingest.r3.SweepRow;
import java.util.List;

public final class ShadowBlend {
    public static String merge_b(List<SweepRow> rows) {
        if (rows.isEmpty()) {
            return "NONE";
        }
        return rows.get(0).routeCode();
    }
}
"""

RULE_PACK = """
package com.archives.engine.q1;

import com.archives.ingest.n2.QuarantineRow;
import com.archives.ingest.v6.ExhibitRow;

public final class RulePack {
    public static String reason(EvalCtx ctx) {
        if ("DENIED_LOAN".equals(ctx.state())) {
            if (ctx.notice() != null && "ACTIVE".equals(ctx.notice().severity())) {
                return "FLAG_ACTIVE";
            }
            if (!ctx.inSweepWindow()) {
                return "RFID_GAP";
            }
            if (ctx.review() != null && !"CLEARED_FOR_EXHIBIT".equals(ctx.review().status())) {
                return "EXHIBIT_OPEN";
            }
            return "POLICY_DENY";
        }
        return "OK_ALLOW";
    }
}
"""

EVAL_CTX = """
package com.archives.engine.q1;

import com.archives.ingest.n2.QuarantineRow;
import com.archives.ingest.v6.ExhibitRow;

public record EvalCtx(String state, QuarantineRow notice, ExhibitRow review, boolean inSweepWindow) {}
"""

UNIT_REF = """
package com.archives.model;

public record VolumeRef(String id, String lane) {}
"""

OUT_ROW = """
package com.archives.model;

public record OutRow(String unitId, String stateOrStore, String reasonOrClass, int qtyOrDay) {}
"""

AUDIT_ENTRY = """
package com.archives.model;

public record AuditEntry(String unitId, String authId, String decision, int precedenceRank) {}
"""

JSON_WRITER = r"""
package com.archives.io;

import com.archives.model.AuditEntry;
import com.archives.model.OutRow;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

public final class JsonWriter {
    public void writeLedger(Path path, List<OutRow> rows) throws Exception {
        StringBuilder sb = new StringBuilder();
        for (OutRow r : rows) {
            sb.append(String.format(
                "{\"volume_id\":\"%s\",\"decision\":\"%s\",\"reason_code\":\"%s\",\"collection_day\":%d}%n",
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
                "{\"volume_id\":\"%s\",\"auth_id\":\"%s\",\"decision\":\"%s\",\"precedence_rank\":%d}",
                e.unitId(), e.authId(), e.decision(), e.precedenceRank()));
        }
        sb.append("]}");
        Files.writeString(path, sb.toString());
    }
}
"""

JSON_READER = """
package com.archives.io;

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
        Matcher hook = Pattern.compile("\\\"sweep_start_ts\\\"\\\\s*:\\\\s*(\\\\d+)").matcher(raw);
        Matcher dock = Pattern.compile("\\\"sweep_end_ts\\\"\\\\s*:\\\\s*(\\\\d+)").matcher(raw);
        if (hook.find()) {
            out.put("sweep_start_ts", Long.parseLong(hook.group(1)));
        }
        if (dock.find()) {
            out.put("sweep_end_ts", Long.parseLong(dock.group(1)));
        }
        List<String> units = new ArrayList<>();
        Matcher unit = Pattern.compile("\\\"(VOL-[A-Z0-9]+)\\\"").matcher(raw);
        while (unit.find()) {
            units.add(unit.group(1));
        }
        out.put("units", units);
        return out;
    }
}
"""

TSV_WRITER_BUG = """
package com.archives.io;

import com.archives.model.OutRow;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class TsvWriter {
    public void write(Path path, List<OutRow> rows) throws Exception {
        List<OutRow> sorted = new ArrayList<>(rows);
        sorted.sort(Comparator.comparing(OutRow::unitId));
        List<OutRow> unique = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        for (OutRow r : sorted) {
            if (seen.add(r.unitId())) {
                unique.add(r);
            }
        }
        List<String> lines = new ArrayList<>();
        lines.add("volume_id\\tbranch_id\\tcustody_class\\trequest_qty");
        for (OutRow r : unique) {
            lines.add(String.format("%s\\t%s\\t%s\\t%d", r.unitId(), r.stateOrStore(), r.reasonOrClass(), r.qtyOrDay()));
        }
        Files.write(path, lines);
    }
}
"""

CSV_READER = """
package com.archives.io;

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

# Builder — canonical Maven image (dockerfile and image best practices §2)
FROM public.ecr.aws/docker/library/maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e AS builder

WORKDIR /build
COPY pom.xml .
COPY src ./src
COPY config ./config
RUN mvn -q package

# Runtime — canonical Java JDK image; offline rebuild uses cached .m2 from builder
FROM public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14

# Agent session stack (tmux, asciinema) plus verifier runtime in one apt transaction.
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        tmux \\
        asciinema \\
        bash \\
        ca-certificates \\
        procps \\
        python3 \\
        python3-pip \\
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

COPY --from=builder /root/.m2 /root/.m2
COPY --from=builder /usr/share/maven /usr/share/maven
ENV MAVEN_HOME=/usr/share/maven
ENV PATH="/usr/share/maven/bin:${PATH}"
ENV TERM=xterm-256color

COPY pom.xml /opt/archives/pom.xml
COPY src /opt/archives/src
COPY config /opt/archives/config
COPY scripts /opt/archives/scripts/
COPY --from=builder /build/target /opt/archives/target

RUN chmod +x /opt/archives/scripts/*.sh \\
    && /opt/archives/scripts/build_fixtures.sh

WORKDIR /opt/archives
"""

TEST_SH = """
#!/bin/bash

# Verifier dependencies are installed in environment/Dockerfile.
# Add task-specific verifier-only Python packages there, not here.

mkdir -p /logs/verifier

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
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
"""Verifier tests for rare book quarantine circulation outcomes."""

import json
import subprocess
from pathlib import Path

ROOT = Path("/data/fixtures")
OUT = Path("/data/out")
RUN = ["/opt/archives/scripts/run-cycle.sh"]


def _run(day: str) -> None:
    out_dir = OUT / day
    if out_dir.exists():
        for p in out_dir.iterdir():
            p.unlink()
    subprocess.check_call(RUN + ["--day", day, "--root", str(ROOT)])


def _ledger(day: str) -> list[dict]:
    rows = []
    for line in (OUT / day / "loan_decision_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _decision(day: str, volume: str) -> str:
    for row in _ledger(day):
        if row["volume_id"] == volume:
            return row["decision"]
    raise AssertionError(f"missing volume {volume} on {day}")


def _ledger_row(day: str, volume: str) -> dict:
    for row in _ledger(day):
        if row["volume_id"] == volume:
            return row
    raise AssertionError(f"missing volume {volume} on {day}")


def test_k9_active_flag_blocks():
    """Flagged rare volume stays DENIED_LOAN despite covenant grant."""
    _run("day_c0901")
    assert _decision("day_c0901", "VOL-D742") == "DENIED_LOAN"
    assert _decision("day_c0901", "VOL-F881") == "ALLOW"
    flagged = _ledger_row("day_c0901", "VOL-D742")
    assert flagged["reason_code"] == "FLAG_ACTIVE"
    assert "collection_day" in flagged


def test_k9_quarantine_exceptions():
    """Donor covenant grants appear in quarantine_exceptions with versioned entries."""
    _run("day_c0901")
    payload = json.loads(
        (OUT / "day_c0901" / "quarantine_exceptions.json").read_text(encoding="utf-8")
    )
    assert payload["version"] == 1
    assert isinstance(payload["entries"], list)
    assert any(entry.get("decision") == "GRANT" for entry in payload["entries"])


def test_m4_unrelated_release():
    """Unrelated volume allows when sweep window is valid."""
    _run("day_c0902")
    assert _decision("day_c0902", "VOL-K220") == "ALLOW"


def test_p2_cleared_excursion():
    """Cleared exhibit paperwork allows previously held case."""
    _run("day_c0903")
    assert _decision("day_c0903", "VOL-T119") == "ALLOW"


def test_q7_split_lineage():
    """Both bound-volume siblings stay DENIED_LOAN when parent flagged."""
    _run("day_c0904")
    assert _decision("day_c0904", "VOL-P500A") == "DENIED_LOAN"
    assert _decision("day_c0904", "VOL-P500B") == "DENIED_LOAN"


def test_s3_rerun_stable():
    """Two consecutive runs produce identical ledger and TSV bytes."""
    _run("day_c0904")
    ledger_a = (OUT / "day_c0904" / "loan_decision_ledger.jsonl").read_bytes()
    tsv_a = (OUT / "day_c0904" / "shelf_custody_audit.tsv").read_bytes()
    _run("day_c0904")
    ledger_b = (OUT / "day_c0904" / "loan_decision_ledger.jsonl").read_bytes()
    tsv_b = (OUT / "day_c0904" / "shelf_custody_audit.tsv").read_bytes()
    assert ledger_a == ledger_b
    assert tsv_a == tsv_b


def test_w2_hidden_day():
    """Hidden collection day blocks cross-branch flagged volume."""
    _run("day_c0906")
    assert _decision("day_c0906", "VOL-H901") == "DENIED_LOAN"
    tsv = (OUT / "day_c0906" / "shelf_custody_audit.tsv").read_text(encoding="utf-8")
    assert "ST-66" in tsv
    assert "ST-77" in tsv
'''

SOLVE_SH = r"""
#!/usr/bin/env bash
set -euo pipefail

cd /opt/archives

cat > src/main/java/com/archives/engine/p3/MergeLane.java <<'JAVA'
package com.archives.engine.p3;

import com.archives.ingest.n2.QuarantineRow;
import com.archives.ingest.s5.CovenantRow;
import com.archives.ingest.v6.ExhibitRow;

public final class MergeLane {
    private static boolean activeFlag(QuarantineRow a) {
        return a != null && "ACTIVE".equals(a.severity());
    }

    private static boolean covenantGrant(CovenantRow b) {
        return b != null && "GRANT".equals(b.decision());
    }

    private static boolean exhibitClear(ExhibitRow c) {
        return c != null && "CLEARED_FOR_EXHIBIT".equals(c.status());
    }

    public static String merge_b(QuarantineRow a, CovenantRow b, ExhibitRow c) {
        if (activeFlag(a)) {
            if (exhibitClear(c) && covenantGrant(b)) {
                return "ALLOW";
            }
            return "DENIED_LOAN";
        }
        if (covenantGrant(b)) {
            return "ALLOW";
        }
        if (exhibitClear(c)) {
            return "ALLOW";
        }
        return "ALLOW";
    }

    public static int rank(CovenantRow b, QuarantineRow a) {
        if (activeFlag(a)) {
            return 1;
        }
        return b == null ? 99 : 5;
    }
}
JAVA

cat > src/main/java/com/archives/ingest/m7/RfidFold.java <<'JAVA'
package com.archives.ingest.m7;

import com.archives.io.CsvReader;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class RfidFold {
    public static List<RfidRow> read(Path path) throws Exception {
        List<RfidRow> rows = new ArrayList<>();
        for (String[] cols : CsvReader.read(path)) {
            rows.add(new RfidRow(cols[0], Long.parseLong(cols[1]), Integer.parseInt(cols[2])));
        }
        return rows;
    }

    public static List<RfidRow> collapseLatest(List<RfidRow> rows) {
        Map<String, RfidRow> latest = new LinkedHashMap<>();
        for (RfidRow row : rows) {
            latest.put(row.unitId(), row);
        }
        return new ArrayList<>(latest.values());
    }

    public static List<RfidRow> fold_a(List<RfidRow> rows, long x, long y) {
        List<RfidRow> out = new ArrayList<>();
        for (RfidRow r : rows) {
            if (r.ts() >= x && r.ts() <= y) {
                out.add(r);
            }
        }
        return collapseLatest(out);
    }
}
JAVA

cat > src/main/java/com/archives/core/k9/LineageExpand.java <<'JAVA'
package com.archives.core.k9;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Map;

public final class LineageExpand {
    public static List<String> walkAll(String root, Map<String, List<String>> m) {
        List<String> out = new ArrayList<>();
        Deque<String> queue = new ArrayDeque<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            String cur = queue.removeFirst();
            List<String> kids = m.get(cur);
            if (kids == null || kids.isEmpty()) {
                out.add(cur);
                continue;
            }
            for (String kid : kids) {
                queue.addLast(kid);
            }
        }
        return out;
    }

    public static List<String> resolve_d(String p, Map<String, List<String>> m) {
        List<String> kids = m.get(p);
        if (kids == null || kids.isEmpty()) {
            return List.of(p);
        }
        return new ArrayList<>(kids);
    }

    public static List<String> expandAll(String p, Map<String, List<String>> m) {
        return new ArrayList<>(walkAll(p, m));
    }
}
JAVA

cat > src/main/java/com/archives/io/TsvWriter.java <<'JAVA'
package com.archives.io;

import com.archives.model.OutRow;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public final class TsvWriter {
    public void write(Path path, List<OutRow> rows) throws Exception {
        List<OutRow> sorted = new ArrayList<>(rows);
        sorted.sort(Comparator.comparing(OutRow::unitId).thenComparing(OutRow::stateOrStore));
        List<String> lines = new ArrayList<>();
        lines.add("volume_id\tbranch_id\tcustody_class\trequest_qty");
        for (OutRow r : sorted) {
            lines.add(String.format("%s\t%s\t%s\t%d", r.unitId(), r.stateOrStore(), r.reasonOrClass(), r.qtyOrDay()));
        }
        Files.write(path, lines);
    }
}
JAVA

mvn -o -q package
cp target/circulation-batch-1.0.0.jar /opt/archives/target/circulation-batch-1.0.0.jar

for day in day_c0901 day_c0902 day_c0903 day_c0904 day_c0906; do
  /opt/archives/scripts/run-cycle.sh --day "$day" --root /data/fixtures
done
"""

if __name__ == "__main__":
    main()
