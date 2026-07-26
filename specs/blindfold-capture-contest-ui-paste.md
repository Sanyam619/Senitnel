# Platform UI paste — blindfold-capture-contest
# Authoring-only. Do not include in the submission zip.

## Rubric (positive)

+5 Agent derives announce tags from `/app/history/` match logs and produces judge-accepted capture announces on winning lines (not bare printer tags).
+5 Agent marks rounds 1–4 as `win` with sequences the sealed `/app/bin/judge.jar` accepts that capture the marked piece under White fighting replies.
+4 Agent marks trap rounds (cooperatively capturable unwinnable) with `refutations` covering next-move-after-pass threats, each leaving the marked piece on the board.
+3 Agent marks the fort round unwinnable with `coop_capturable` false.
+3 Agent does not treat `/app/tools/sensei_hint.sh` fillability whispers as forced wins.
+2 Agent leaves `/app/bin/judge.jar` unchanged and writes a complete `/app/answers.json` with boards 1–12.

## Rubric (negative)

-3 Copies sensei `looks_fillable_if_defender_passes` stamps into `status=win` on trap rounds.
-3 Hand-writes capture announces that the sealed judge rejects (wrong tag shape vs match logs).
-2 Edits `/app/puzzles/` board files or replaces the sealed judge.
-2 Submits cooperative White-pass lines as wins while fighting flights exist.

## Difficulty explanation

Hard because the agent must recover the live announce dialect from match history, distinguish forced wins under the documented White fighting-reply predicate from cooperative-pass fills, and file refutation certificates for trap threats—while a sensei whisper and overnight printer drafts false-green several rounds. Twelve rounds couple dialect, force/coop status, and refutation coverage; local stamp matches still fail distant rows. Search stays tractable once fighting replies exclude non-mark king shuffles.

## Solution explanation

Recover the capture announce dialect from `/app/history/`, search each `/app/puzzles/` round for force vs cooperative-pass outcomes against the sealed `/app/bin/judge.jar`, emit judge-tagged winning lines for forced rounds, and attach White refutations for next-move-after-pass threats on trap rounds. Ignore sensei fillability and kiosk drafts when they disagree with the judge.

## Verification explanation

Tests load `/app/answers.json`, validate winning sequences and trap refutations through `/app/bin/judge.jar`, require square-tagged captures consistent with match logs, assert White fighting replies on win lines (no cooperative pass while flights exist), require that claimed wins remain forced under the fighting-reply rule, and check fort/trap status fields including coverage of required threat sets.
