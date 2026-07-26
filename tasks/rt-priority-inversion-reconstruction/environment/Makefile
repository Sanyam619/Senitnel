CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -Iinclude
LDFLAGS =

SIM_OBJS = src/sim/core.o src/sim/queue.o src/sim/lock.o src/sim/deadline.o src/sim/replay.o src/sim/util.o
PROBE_OBJS = src/probe/main.o src/probe/stage_a.o src/probe/stage_b.o kern/a7/weave.o kern/a7/hash.o relay/m3/latch.o relay/m3/shadow.o span/q9/span.o span/q9/ring.o lift/w2/lift.o $(SIM_OBJS)

all: kernprobe

kernprobe: $(PROBE_OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

klreplay-vendor: $(SIM_OBJS)
	@test -f /tmp/klreplay_main.c
	$(CC) $(CFLAGS) -o klreplay /tmp/klreplay_main.c $(SIM_OBJS) $(LDFLAGS)

clean:
	rm -f kernprobe klreplay $(SIM_OBJS) $(PROBE_OBJS)

.PHONY: all clean klreplay-vendor
