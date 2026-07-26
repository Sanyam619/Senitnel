# Talking to the sealed table judge

`/app/bin/judge.jar` is the referee for this booklet. It replays tries, rules on
legality, and reports ejections. It never rates a round — verdicts are yours.

```
java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt
java -jar /app/bin/judge.jar legal --board /app/puzzles/board_01.txt --side black
java -jar /app/bin/judge.jar apply --board /app/puzzles/board_01.txt --move 'c3>d3'
java -jar /app/bin/judge.jar apply --board /app/puzzles/board_01.txt --side white --move 'e1>d1'
java -jar /app/bin/judge.jar validate --board /app/puzzles/board_01.txt \
  --line 'black c3d3>e3;white a1>b1;black e3>e2'
```

- `view` prints marble counts, whether the floor is already met, and Black's
  legal turns.
- `legal` lists a colour's legal turns in `c3d3>e3` form.
- `apply` replays one turn for one colour and reports legality plus ejection
  fields afterwards.
- `validate` replays a whole line of colour-tagged turns and reports
  `all_legal`, `black_turns`, `ejected`, and `enclosed`. Friendly lines may
  list several Black turns in a row; forcing lines alternate colours.

The judge is sealed. Leave it and the round sheets alone: the table checks the
jar at `/app/bin/judge.jar` against its own sealed copy at
`/opt/tbench/judge.jar`. The overnight kiosk drafts and the sensei whisper are
surface readings, not the table's word.
