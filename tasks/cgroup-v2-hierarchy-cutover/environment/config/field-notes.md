# lab cgroup cutover field notes

Parallel tree roots live under the data partition cgroup layout.
Root controller advertisement can disagree with slice delegation state.
v1 hierarchies may retain per-controller directory shadows for unmigrated units.
Ledger tools read end state; they do not perform migration by themselves.
