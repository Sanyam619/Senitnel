# Talking to the sealed table judge

`/app/bin/judge.jar` is the referee for this booklet. It replays tries, rules on
legality, and reports exclusive territory. It never rates a round — verdicts
are yours.

```
java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt
java -jar /app/bin/judge.jar legal --board /app/puzzles/board_01.txt --side white
java -jar /app/bin/judge.jar territory --board /app/puzzles/board_01.txt
java -jar /app/bin/judge.jar apply --board /app/puzzles/board_01.txt --move 'a1-a2/a3'
java -jar /app/bin/judge.jar apply --board /app/puzzles/board_01.txt --side black --move 'e5-e4/e3'
java -jar /app/bin/judge.jar validate --board /app/puzzles/board_01.txt \
  --line 'white a1-a2/a3;black e5-e4/e3;white a2-b2/a2'
```

- `view` prints the grid as the table reads it, exclusive counts, the delta,
  whether the floor is already met, and White's legal turns.
- `legal` lists a colour's legal turns in `a4-b3/c2` form.
- `territory` reports `white_excl`, `black_excl`, `territory_delta`, and
  `enclosed`.
- `apply` replays one turn for one colour and reports legality plus the
  territory fields afterwards.
- `validate` replays a whole line of colour-tagged turns and reports
  `all_legal`, `white_turns`, and the final territory fields. Friendly lines
  may list several White turns in a row; forcing lines alternate colours.

The judge is sealed. Leave it and the round sheets alone: the table checks the
jar at `/app/bin/judge.jar` against its own sealed copy at
`/opt/tbench/judge.jar`. The overnight kiosk drafts and the sensei whisper are
surface readings, not the table's word.
