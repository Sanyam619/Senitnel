# Mill floors

Successful mill play for this booklet means White completes at least one
mill inside the round's `moves_left` budget:

```
MILL_FLOOR = 1
```

`mill_in` on the score card must equal the true number of mills White
formed on the plan being reported. A cooperative plan that closes one mill
reports `mill_in = 1`. A forcing line that closes one mill reports
`mill_in = 1`. A fort reports `mill_in = 0`.

Padding is refused: filing a longer swing that forms an extra mill and
later breaks it to inflate `mill_in` does not satisfy the floor and fails
the table's mill-count check.
