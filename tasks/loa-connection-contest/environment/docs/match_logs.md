# Match logs

Sample table sessions live under `/app/history/`. Each log is a short
recorded exchange with the sealed judge on a scratch position, kept so
newcomers can see the dialect the table speaks: how `validate` reports each
step, when `black_connected` flips, how the group counts move as pieces are
taken, and how an illegal step is turned away.

These are demonstration positions on throwaway boards, not the contest
rounds. Use them to learn the judge's replies, then read the real rounds
under `/app/puzzles/` yourself. The judge's report — not a printer draft or a
sensei whisper — is the authority on what actually happened on the board.

The logs also show the two ways a move gets turned away: a travel length that
does not match the count on the line it is using, and a travel that would
have to step over an enemy piece to arrive.
