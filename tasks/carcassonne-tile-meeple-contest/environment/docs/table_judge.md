# Talking to the sealed table judge

`/app/bin/judge.jar` is the referee for this booklet. It replays tries, rules on
legality, and reports scores. It never rates a round — verdicts are yours.

```
java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt
java -jar /app/bin/judge.jar legal --board /app/puzzles/board_01.txt --side red
java -jar /app/bin/judge.jar apply --board /app/puzzles/board_01.txt --move 'FFCF@b3:0+city:S'
java -jar /app/bin/judge.jar apply --board /app/puzzles/board_01.txt --side blue --move 'pass'
java -jar /app/bin/judge.jar validate --board /app/puzzles/board_01.txt \
  --line 'red FFCF@b3:0+city:S'
```

- `view` prints score, floor, budget, and how many Red legal turns exist.
- `legal` lists a side's legal turns.
- `apply` replays one turn and reports legality plus score afterwards.
- `validate` replays a whole line of colour-tagged turns and reports
  `all_legal`, `red_turns`, `score`, and `enclosed` (whether the floor was met).
  Friendly lines may list several Red turns in a row; forcing lines alternate
  colours.

The judge is sealed. Leave it and the round sheets alone: the table checks the
jar at `/app/bin/judge.jar` against its own sealed copy at
`/opt/tbench/judge.jar`. The overnight kiosk drafts and the sensei whisper are
surface readings, not the table's word.
