# Reversi marked-disc tournament

Write `/app/answers.json` covering eleven Black-to-move rounds. Each round sheet
marks one White disc. For every round, decide whether three Black stone drops
turn that disc Black against a White that fights to keep it, whether the take is
there with White passing every turn, and — on rounds White can hold — which White
reply answers each of Black's threats.

Card vocabulary: rounds, board_id, status, line, refutations. The verdict words,
the three-stone budget, White's fighting replies, fort shapes, threat coverage,
and the announce customs every called drop carries — the flips: call and its
corner form — are documented under `/app/docs/`.

An overnight kiosk printed a draft card the table has thrown out, and the sensei
whisper only listens for a loud single drop. Match logs under `/app/history/`
show the dialect the table expects for called drops.

Rounds: `/app/puzzles/`. Kiosk draft: `/app/kiosk/draft_card.json`. Whisper:
`/app/tools/sensei_hint.sh`. Sealed judge: `/app/bin/judge.jar`. Leave the sealed
judge and the round sheets unchanged.
