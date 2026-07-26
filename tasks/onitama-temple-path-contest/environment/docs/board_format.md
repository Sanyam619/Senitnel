# Board format

Each round sheet under `/app/puzzles/` looks like:

```
board_id: 01
to_move: sensei
mate_budget: 3
sensei_cards: Tiger,Crab
pupil_cards: Dragon,Frog
sideboard: Rabbit
board:
s.S.s
.....
.....
.....
p.P.p
```

Five rows of five characters, **rank 1 first** (Sensei's back rank), then up to
rank 5. Files `a`..`e` left to right. Cells: `.` empty, `s` Sensei student,
`S` Sensei master, `p` Pupil student, `P` Pupil master.

Temples: Sensei `c1`, Pupil `c5`.

Move tokens are colour-tagged: `sensei Tiger:c2-c4` or `pupil Crab:a4-c4`.
