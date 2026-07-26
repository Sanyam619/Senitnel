# Platform UI paste — superko-rule-forensics (Weiqi capture tournament)
# Authoring-only. Do not include in the submission zip.
# Rubric source of truth: specs/superko-rule-forensics-rubric.txt

## Rubric (paste verbatim)

Agent reads /app/docs/ house rules and /app/history/ match books to recover the live ko family from superko refusal colours, +3
Agent repairs overnight printer sources under /app/kiosk/ so python -m kiosk doctor reports a printer_ko_guess that matches the live table family, +5
Agent repairs the printer so doctor keeps sensei-green White-pass trap rounds as unwinnable with coop_capturable true (printer_round_5 sample), +5
Agent repairs printer reply certificates so python -m kiosk emit files White liberty stone replies that leave the target occupied on trap rounds, +5
Agent validates candidate lines with java -jar /app/bin/judge.jar while building the card, +3
Agent writes /app/answers.json covering boards 1..12 with the live ko rule, forced-win sequences that empty the target under White stone replies, and trap/fort statuses with coop_capturable and refutations where required, +5
Agent leaves /app/bin/judge.jar unchanged and does not rewrite /app/puzzles/ or /app/history/ to force outcomes, +2
Agent marks sensei-green White-pass trap rounds as status win in /app/answers.json, -5
Agent hand-writes /app/answers.json while leaving python -m kiosk doctor or emit disagreeing with the sealed table, -5
Agent edits or replaces /app/bin/judge.jar, -5
Agent files only white pass replies in trap refutations when a liberty stone reply keeps the target, -3
Agent submits win sequences that rely on cooperative White passes while a legal liberty play still keeps the target, -3

## Difficulty explanation

Hard because the agent must recover the live ko family from match-log refusal colours, repair three interacting overnight-printer divergences (ko guess, trap-vs-win stamp, liberty reply certificates), and produce a full tournament card whose win lines and trap refutations survive the sealed judge under fighting White replies. Sensei whispers and broken printer drafts false-green several rounds; hand-written cards fail when doctor/emit still disagree with the table.

## Solution explanation

Read match books and house docs to identify the live ko family, patch the overnight printer under /app/kiosk/ until doctor/emit agree with the sealed judge on ko family, trap stamps, and stone refutations, then derive /app/answers.json (wins with White resistance; unwinnable traps with per-liberty refutations; fort with coop_capturable false) validated through /app/bin/judge.jar.

## Verification explanation

Tests load /app/answers.json, require the live ko family, validate win sequences and trap refutations through /app/bin/judge.jar, reject cooperative White-pass wins, require trap/fort coop_capturable semantics, and re-run python -m kiosk doctor/emit so a hand-written card cannot pass while the printer still diverges.
