import json
import subprocess
from pathlib import Path


APP = Path("/app")
OUT = APP / "output"


def run_console(scenarios_dir=None):
    scenarios = scenarios_dir or (APP / "scenarios")
    subprocess.run(["bash", str(APP / "build.sh")], check=True, cwd=APP)
    if OUT.exists():
        for path in OUT.glob("*.json"):
            path.unlink()
    subprocess.run(
        [
            "java",
            "-cp",
            str(APP / "build/classes"),
            "com.acme.ops.Console",
            str(scenarios),
            str(OUT),
        ],
        check=True,
        cwd=APP,
    )
    with (OUT / "decisions.json").open() as f:
        decisions = json.load(f)
    with (OUT / "compensations.json").open() as f:
        compensations = json.load(f)
    return decisions, compensations


def decision(doc, scenario, txid):
    return doc["scenarios"][scenario]["transactions"][txid]["decision"]


def actions(doc, scenario, group):
    return doc["scenarios"][scenario]["sagas"][group]["actions"]


def journal_transaction_ids(scenario_dir):
    ids = set()
    for path in scenario_dir.glob("*.log"):
        for line in path.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "TX":
                ids.add(parts[1])
    return ids


def saga_ids(scenario_dir):
    ids = []
    for line in (scenario_dir / "saga.plan").read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "SAGA":
            ids.append(parts[1])
    return ids


def write_verify_drill(root):
    scenario = root / "verify-drill"
    scenario.mkdir(parents=True, exist_ok=True)
    (scenario / "meta.properties").write_text(
        "mode=PC\nmembers=alpha,beta,gamma\n",
        encoding="utf-8",
    )
    (scenario / "coordinator.log").write_text(
        "\n".join(
            [
                "TX t-flush DECISION COMMIT",
                "TX t-stop DECISION COMMIT",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (scenario / "member-alpha.log").write_text(
        "\n".join(
            [
                "TX t-flush PREPARED",
                "TX t-done PREPARED",
                "TX t-done COMMITTED",
                "TX t-full PREPARED",
                "TX t-part PREPARED",
                "TX t-stop PREPARED",
                "TX t-stop ABORTED",
                "TX t-clash PREPARED",
                "TX t-clash COMMITTED",
                "TX t-echo PREPARED",
                "TX t-echo PREPARED",
                "TX t-echo PREPARED",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (scenario / "member-beta.log").write_text(
        "\n".join(
            [
                "TX t-flush PREPARED",
                "TX t-done PREPARED",
                "TX t-full PREPARED",
                "TX t-part PREPARED",
                "TX t-stop PREPARED",
                "TX t-clash PREPARED",
                "TX t-clash ABORTED",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (scenario / "member-gamma.log").write_text(
        "\n".join(
            [
                "TX t-flush PREPARED",
                "TX t-full PREPARED",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (scenario / "saga.plan").write_text(
        "\n".join(
            [
                "SAGA sg-flush TX t-flush",
                "STEP reserve APPLIED undo-reserve",
                "STEP bill APPLIED undo-bill",
                "SAGA sg-done TX t-done",
                "STEP hold APPLIED undo-hold",
                "SAGA sg-part TX t-part",
                "STEP gate APPLIED undo-gate",
                "STEP notify APPLIED undo-notify",
                "STEP ledger COMPENSATED undo-ledger",
                "SAGA sg-stop TX t-stop",
                "STEP debit APPLIED undo-debit",
                "SAGA sg-clash TX t-clash",
                "STEP open APPLIED undo-open",
                "STEP skip SKIPPED undo-skip",
                "STEP close APPLIED undo-close",
                "SAGA sg-echo TX t-echo",
                "STEP pulse APPLIED undo-pulse",
                "SAGA sg-ghost TX t-ghost",
                "STEP draft APPLIED undo-draft",
                "STEP wait PENDING undo-wait",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return scenario


def write_pa_drill(root):
    scenario = root / "pa-drill"
    scenario.mkdir(parents=True, exist_ok=True)
    (scenario / "meta.properties").write_text(
        "mode=PA\nmembers=east,west\n",
        encoding="utf-8",
    )
    (scenario / "coordinator.log").write_text("", encoding="utf-8")
    (scenario / "member-east.log").write_text(
        "TX p-all PREPARED\nTX p-one PREPARED\nTX p-one COMMITTED\n",
        encoding="utf-8",
    )
    (scenario / "member-west.log").write_text(
        "TX p-all PREPARED\n",
        encoding="utf-8",
    )
    (scenario / "saga.plan").write_text(
        "\n".join(
            [
                "SAGA sg-pa-all TX p-all",
                "STEP grab APPLIED undo-grab",
                "SAGA sg-pa-one TX p-one",
                "STEP keep APPLIED undo-keep",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return scenario


def test_north_completed_move_stays_committed():
    """A participant completion must not be replaced by a later prepared row from another journal."""
    decisions, _ = run_console()
    assert decision(decisions, "north", "n-004") == "COMMIT"


def test_harbor_legacy_flush_still_commits():
    """An older harbor transfer with a flushed global row should remain committed."""
    decisions, _ = run_console()
    assert decision(decisions, "harbor", "h-210") == "COMMIT"


def test_vault_inflight_saga_needs_cleanup():
    """A vault saga bound to an aborted in-flight transfer should still list pending undo work."""
    decisions, compensations = run_console()
    assert decision(decisions, "vault", "v-903") == "ABORT"
    assert actions(compensations, "vault", "sg-vault-3") == ["undo-reserve"]


def test_north_member_completion_survives_gap():
    """A one-sided completed member row should keep an unflushed north id durable."""
    decisions, _ = run_console()
    assert decision(decisions, "north", "n-005") == "COMMIT"


def test_north_prepared_only_falls_back():
    """Prepared-only north rows should not be promoted by the default drill mode."""
    decisions, _ = run_console()
    assert decision(decisions, "north", "n-002") == "ABORT"


def test_harbor_full_prepared_set():
    """The harbor drill promotes a complete prepared set when no global row flushed."""
    decisions, _ = run_console()
    assert decision(decisions, "harbor", "h-211") == "COMMIT"


def test_harbor_partial_prepared_set():
    """The harbor drill rejects a prepared set that is missing a member row."""
    decisions, _ = run_console()
    assert decision(decisions, "harbor", "h-212") == "ABORT"


def test_vault_flushed_rows_still_win():
    """Flushed vault decisions should remain present in the output."""
    decisions, _ = run_console()
    assert decision(decisions, "vault", "v-900") == "COMMIT"
    assert decision(decisions, "vault", "v-901") == "ABORT"


def test_abort_cleanups_are_reverse_and_filtered():
    """Cleanup plans should reverse applied steps and skip completed cleanup rows."""
    _, compensations = run_console()
    assert actions(compensations, "north", "sg-north-1") == ["undo-pick", "undo-reserve"]
    assert actions(compensations, "harbor", "sg-harbor-2") == ["undo-notify", "undo-gate"]
    assert actions(compensations, "vault", "sg-vault-1") == ["undo-notify", "undo-debit"]


def test_commit_cleanups_are_empty():
    """Durable saga work should keep saga entries with no cleanup actions."""
    _, compensations = run_console()
    for scenario, group in (
        ("north", "sg-north-2"),
        ("harbor", "sg-harbor-1"),
        ("vault", "sg-vault-2"),
        ("delta", "sg-delta-keep"),
        ("delta", "sg-delta-full"),
    ):
        assert group in compensations["scenarios"][scenario]["sagas"]
        assert actions(compensations, scenario, group) == []


def test_outputs_cover_every_scenario():
    """Both artifacts should list every drill scenario name."""
    decisions, compensations = run_console()
    assert set(decisions["scenarios"]) == {"north", "harbor", "vault", "delta"}
    assert set(compensations["scenarios"]) == {"north", "harbor", "vault", "delta"}


def test_delta_divergent_members_abort():
    """Conflicting terminal member rows for one transfer must resolve to abort."""
    decisions, compensations = run_console()
    assert decision(decisions, "delta", "d-split") == "ABORT"
    assert actions(compensations, "delta", "sg-delta-split") == ["undo-push", "undo-stage"]


def test_delta_repeated_prepared_is_not_quorum():
    """Repeated prepared lines on one member must not invent a full participant set."""
    decisions, compensations = run_console()
    assert decision(decisions, "delta", "d-dup") == "ABORT"
    assert actions(compensations, "delta", "sg-delta-dup") == ["undo-release", "undo-hold"]


def test_delta_ghost_transfer_from_saga_plan():
    """A saga-bound transfer missing from every journal still needs a decision and cleanup."""
    decisions, compensations = run_console()
    assert decision(decisions, "delta", "d-ghost") == "ABORT"
    assert actions(compensations, "delta", "sg-delta-ghost") == ["undo-draft"]


def test_delta_full_prepared_commits():
    """A complete prepared set in the delta drill should commit without cleanup."""
    decisions, compensations = run_console()
    assert decision(decisions, "delta", "d-full") == "COMMIT"
    assert decision(decisions, "delta", "d-keep") == "COMMIT"
    assert actions(compensations, "delta", "sg-delta-full") == []


def test_synthetic_scenario_replays_inputs(tmp_path):
    """A verifier-built drill should replay every journal and saga input into both artifacts."""
    scenario = write_verify_drill(tmp_path)
    expected_tx = journal_transaction_ids(scenario) | {"t-ghost"}
    expected_sagas = saga_ids(scenario)

    decisions, compensations = run_console(scenarios_dir=tmp_path)

    assert set(decisions["scenarios"]) == {"verify-drill"}
    assert set(compensations["scenarios"]) == {"verify-drill"}
    assert set(decisions["scenarios"]["verify-drill"]["transactions"]) == expected_tx
    assert set(compensations["scenarios"]["verify-drill"]["sagas"]) == set(expected_sagas)

    assert decision(decisions, "verify-drill", "t-flush") == "COMMIT"
    assert decision(decisions, "verify-drill", "t-done") == "COMMIT"
    assert decision(decisions, "verify-drill", "t-full") == "COMMIT"
    assert decision(decisions, "verify-drill", "t-part") == "ABORT"
    assert decision(decisions, "verify-drill", "t-stop") == "ABORT"
    assert decision(decisions, "verify-drill", "t-clash") == "ABORT"
    assert decision(decisions, "verify-drill", "t-echo") == "ABORT"
    assert decision(decisions, "verify-drill", "t-ghost") == "ABORT"

    assert actions(compensations, "verify-drill", "sg-flush") == []
    assert actions(compensations, "verify-drill", "sg-done") == []
    assert actions(compensations, "verify-drill", "sg-part") == ["undo-notify", "undo-gate"]
    assert actions(compensations, "verify-drill", "sg-stop") == ["undo-debit"]
    assert actions(compensations, "verify-drill", "sg-clash") == ["undo-close", "undo-open"]
    assert actions(compensations, "verify-drill", "sg-echo") == ["undo-pulse"]
    assert actions(compensations, "verify-drill", "sg-ghost") == ["undo-draft"]


def test_pa_mode_rejects_full_prepared_set(tmp_path):
    """A non-PC drill must not promote a complete prepared set without terminal evidence."""
    write_pa_drill(tmp_path)
    decisions, compensations = run_console(scenarios_dir=tmp_path)
    assert decision(decisions, "pa-drill", "p-all") == "ABORT"
    assert decision(decisions, "pa-drill", "p-one") == "COMMIT"
    assert actions(compensations, "pa-drill", "sg-pa-all") == ["undo-grab"]
    assert actions(compensations, "pa-drill", "sg-pa-one") == []
