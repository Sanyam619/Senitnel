# Talking to the sealed table judge

`/app/bin/judge.jar` is the referee for this booklet. It replays tries, rules on
legality, and reports scores. It never rates a round — verdicts are yours.

```
java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt
java -jar /app/bin/judge.jar legal --board /app/puzzles/board_01.txt --side trader
java -jar /app/bin/judge.jar apply --board /app/puzzles/board_01.txt --move 'take:clo'
java -jar /app/bin/judge.jar apply --board /app/puzzles/board_01.txt --side rival --move 'sell:lea:1'
java -jar /app/bin/judge.jar validate --board /app/puzzles/board_01.txt \
  --line 'trader take:clo;rival sell:lea:1;trader sell:clo:3'
```

- `view` prints the market, hands, herds, floor, seal, whether the floor is
  already met, and the Trader's legal actions.
- `legal` lists a side's legal actions.
- `apply` replays one action for one side and reports legality plus score
  afterwards.
- `validate` replays a whole line of side-tagged actions and reports
  `all_legal`, `trader_turns`, `score`, `goal_met`, and `claimed`. Friendly
  lines may list several Trader actions in a row; forcing lines alternate
  sides when the Rival answers.

The judge is sealed. Leave it and the round sheets alone: the table checks the
jar at `/app/bin/judge.jar` against its own sealed copy at
`/opt/tbench/judge.jar`. The overnight kiosk drafts and the sensei whisper are
surface readings, not the table's word.
