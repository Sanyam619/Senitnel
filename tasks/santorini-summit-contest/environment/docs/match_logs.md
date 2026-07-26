# Match logs

Scratch sessions under `/app/history/` show how the sealed judge speaks on
throwaway boards. They are not contest rounds and are not an answer key.

Typical validate line:

```
java -jar /app/bin/judge.jar validate --board /app/history/game_01.txt \
    --moves "F:b2-c3"
```

Expect JSON with `all_legal` and `summit` when the line is a clean ascent.
