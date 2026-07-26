### Decision
GO — Attempt 1. Same as authoring spec.

### Why GO
Primary activity is a Blokus packing tournament under a sealed referee — open
`games` category. Graded fields are play facts (status, forcing vs friendly
lines, threat replies, squares_left after replay), not SE metric formulas.
Hardness: corner-only adjacency × inventory × forced vs coop fill; sensei and
kiosk are false-green bait.

### Discovery budget (solver must extract)
1. Corner-touch-only same-colour adjacency and edge-touch illegality — live in
   `/app/docs/contest_rules.md` + sealed judge `legal`/`apply`; instruction
   must not paste a placement recipe.
2. Inventory-threatening first placements and required ⊆ submitted refutation
   coverage — live in docs + verifier recomputation; instruction stays
   symptoms-only.
3. Sensei bounding-box fit and kiosk fourth-placement win stamp are not
   authoritative — live in tools/kiosk behavior; instruction names them as
   surface drafts only.

### Topology distribution
1. Search engine + sheet parser + card writer (oracle packages).
2. Sealed judge replay + independent test engine + emit-twice kiosk check.
3. Docs contract (floor/budget/threats) + puzzle fixtures + history dialect.

### Residual risks
Frontier agents that write a correct Blokus engine in-container may still clear
the booklet; hardness relies on trap/fort matrix and false-green bait, same
class as other sealed-judge contests. Category risk if instruction/oracle smell
like SE — mitigated by bash languages, tournament tags, desk package names.
