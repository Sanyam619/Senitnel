# Architecture

The warmup host reconciles three authorities for each guest call site
before emitting the isolation report.

## Authorities

1. **Profile tape** (`data/authority/profile/*.prof`) — probe-batch
   durable view: heat probes, polymorphic flag, epoch stamp, trust mark,
   and whether probes overlapped a registry reload.
2. **Rebind journal** (`data/authority/rebind/*.rbnd`) — import-signature
   old/new shape (type, arity, bounds, table) after a module-registry
   event.
3. **Floor hints** (`data/authority/floor/*.flr`) — surface policy
   suggestions from a soft health probe (diagnostic only).

The signed registry epoch lives at `data/manifest/registry.sig`. Scenario
heat / host-attempt flags live under `data/scenarios/`.

## Pipeline

- Tier A folds a profile tape row into a durable slot.
- Tier B folds a rebind journal row into a signature-delta slot.
- Tier C applies the admission policy in `docs/authority-notes.md`.

## Epoch views

The profile stamp records registry time at probe collection. The decision
epoch is the registry view at evaluation (manifest epoch, advanced when
the scenario triggers a reload). After a reload window those two values
can disagree even when the rebind journal shows no shape delta.
