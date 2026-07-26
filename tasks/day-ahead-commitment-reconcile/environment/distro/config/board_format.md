# Board format

Each board under `/data/fixtures/board_XX.txt` lists:

- `round_id`
- `demand_mw`
- `reserve_mw`
- one or more `unit ID CAPACITY OFFER` lines

A commitment assigns positive MW to listed units within capacity. Energy-feasible lines sum exactly to demand. Online units are those with positive MW. Reserve headroom is leftover capacity on online units.
