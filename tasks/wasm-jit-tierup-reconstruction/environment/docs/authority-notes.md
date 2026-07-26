# Admission Policy (authoritative)

This document is the authoritative admission decision policy for the
warmup host. Floor hints are diagnostic only and never decide admit,
hold, or refuse.

## Inputs

- Scenario heat: `is_hot`, `is_very_hot`, `triggers_reload`,
  `attempts_host_call`, `host_is_legit`, `live_table`
- Profile fold: durable `has_profile`, `polymorphic`, `trustworthy`,
  `epoch_stamp`
- Rebind fold: per-dimension deltas (`type`, `arity`, `bounds`, `table`)
  and aggregate `signature_changed` (true if **any** dimension differs)
- Manifest epoch from `/app/data/manifest/registry.sig`
- Decision epoch: equal to the manifest epoch, advanced by one when the
  scenario has `triggers_reload=1`

## Profile trust rule

`trust_mark` on the tape is not authoritative when `reload_seen=1`.
A probe batch that straddled a registry reload must fold to
`trustworthy=0`. Otherwise the durable bit may follow a clean tape mark.

## Precedence (highest first)

Evaluate in this order. Stop at the first matching rule.

1. **Cold refuse** — if `is_hot=0`:
   - `outcome=refused`
   - `category=interpreter_only`
   - `host_call_permitted=false`
   - `checks_installed=[]`

2. **Polymorphic hold** — if the site has a profile and is polymorphic:
   - `outcome=held`
   - `category=held_polymorphic`
   - `host_call_permitted=false`
   - `checks_installed=["type"]`
   - Floor promote hints must not override this rule.

3. **Warm but not very-hot hold** — if `is_hot=1` and `is_very_hot=0`:
   - `outcome=held`
   - `host_call_permitted=false`
   - `checks_installed=[]`

4. **Missing profile hold** — if `has_profile=0` on a hot/very-hot site:
   - `outcome=held`
   - `host_call_permitted=false`
   - `checks_installed` = all four guards

5. **Refresh / rebind concern** — if any of:
   - profile `epoch_stamp` ≠ decision epoch
   - profile `trustworthy=0`
   - rebind `signature_changed=1`

   then install **all four** guards (`type`, `arity`, `bounds`, `table`) and:

   - If any shape dimension changed, **hold**:
     - `outcome=held`
     - `host_call_permitted=false`
     - `category` = the first changed dimension among
       `type` → `type_bypass_blocked`,
       `arity` → `arity_bypass_blocked`,
       `bounds` → `bounds_bypass_blocked`,
       `table` → `table_bypass_blocked`
   - Else (epoch skew and/or untrustworthy with **no** shape bypass):
     - `outcome=promoted`
     - `category=benign_epoch_bumped`
     - `checks_installed` = all four
     - `host_call_permitted=true` iff `attempts_host_call=1` and
       `host_is_legit=1`

6. **Stable promote** — otherwise:
   - `outcome=promoted`
   - `checks_installed=[]`
   - if `live_table>0` and `attempts_host_call=0`:
     `category=benign_table_stable` and `host_call_permitted=false`
   - else:
     `category=benign_type_stable` and
     `host_call_permitted=true` iff `attempts_host_call=1` and
     `host_is_legit=1`

## Non-negotiables

- Do not rewrite authority fixtures to force agreement.
- Soft/surface checks (including floor hints and `fastcheck`) do not
  authorize host crossings.
- Report `scenarios` must be sorted by `id` ascending.
- `registry_epoch` in the report equals the signed manifest epoch (not
  the per-site decision epoch).
