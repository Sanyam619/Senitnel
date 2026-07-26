# Board sheet format

Each `/app/puzzles/board_XX.txt` sheet uses:

```
board_id: 01
to_move: trader
floor: 12
budget: 3
seal: 5
market: clo,lea,cam,spi,sil
deck: lea,spi,cam,clo
hand: clo,clo
herd: 0
rival_hand: lea
rival_herd: 2
tokens:
lea: 4,3,2,1
spi: 5,3,2,1
clo: 5,3,2,1
sil: 5,5,5
gol: 6,6,5
dia: 7,7,5
bonus3: 2,3,1
bonus4: 4,5
bonus5: 8
```

Market always lists five cards. Deck order is the refill order after takes and
herd sweeps. Token stacks are top-first.
