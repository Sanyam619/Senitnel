# Scenario field notes

Operator observations from post-crash readback. Symptoms only.

## shard_a

`/notes.txt` and `/config/app.cfg` disagree with what the last sealed redo batch should have left on disk.

## shard_b

A retired path's bytes reappear after another live path reused the same physical block.

## shard_c

The two volume headers disagree on epoch versus durable watermark. Ledger vs audit extracts change depending on which header a tool trusts.

## shard_d

`/cache.bin` content and the free-block map do not agree after a sealed cleanup.

## shard_e

One header advertises a much larger epoch while marked non-primary. Tools that still treat that header as authoritative return wrong archive bytes.

## shard_f

Sealed redo for `/order.dat` is present, but readback still shows pre-update content depending on replay order assumptions.

## shard_g

`/hold.dat` oscillates between baseline and a later incomplete write across recovery attempts.

## shard_h

`/layer.dat` still reads an intermediate layer after a sealed transaction that touched the same block more than once.

## shard_i

Headers stopped advancing their durable watermark, yet later sealed redo for `/lag.dat` is still in the circular area.

## shard_j

`/keep.dat` loses its sealed payload when recovery honours a forget that never finished committing.
