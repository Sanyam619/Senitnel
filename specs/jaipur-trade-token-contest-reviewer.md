### Reviewer appendix — jaipur-trade-token-contest

Collapse WARN justifications (Step 3b):

- **RC1/RC7/GX3:** Oracle is search-derived card emission (~67 LOC wrappers +
  substantive engine). GX3 real edit distance is substantive (513). Games
  booklet pattern, not sed polarity.
- **RC2:** `board_hunt` / `card_out` names are opaque oracle package roots used
  across contest tasks; instruction nouns do not name those paths as fix
  recipes.
- **RC3:** Format/structure asserts sit beside domain verdict/replay checks;
  hardness lives in win/trap/fort + refutations + judge score/tokens.
- **RC8:** Oracle packages split desk_books / board_hunt / card_out; concentration
  WARN is the shared contest layout.
- **CR1/CR2/CR7/CR8:** Spec carries symbol_table + flipping_point_contract;
  evidence sidecar optional for this games booklet (same class as blokus/
  carcassonne).

Local Step 2b evidence:
- `./scripts/check-task.sh` PASS (collapse WARN justified)
- harbor oracle Mean **1.000** (`jobs/2026-07-26__19-16-02`)
- harbor nop Mean **0.000** (`jobs/2026-07-26__19-16-45`)

Fixture spread: 4 win / 5 trap / 3 fort. Languages `["bash"]`. Category
`games`. Output `/output/jaipur-card.json`.
