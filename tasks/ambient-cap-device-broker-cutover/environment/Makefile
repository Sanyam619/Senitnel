CC = gcc
CFLAGS = -Wall -Wextra -O2 -I. -Iinclude
LIBS = lib/state_io.c lib/path_util.c lane/apply_lane_a.c lane/legacy_lane.c seat/seat_slot_b.c seat/probe_node.c roll/emit_rollup_c.c

BINDIR = bin

all: $(BINDIR)/topsurf $(BINDIR)/nsprobe $(BINDIR)/laneapply $(BINDIR)/nodeseat $(BINDIR)/racepulse $(BINDIR)/ledgerout

$(BINDIR):
	mkdir -p $(BINDIR)

$(BINDIR)/topsurf: cmd/topsurf/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/topsurf/main.c $(LIBS)

$(BINDIR)/nsprobe: cmd/nsprobe/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/nsprobe/main.c $(LIBS)

$(BINDIR)/laneapply: cmd/laneapply/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/laneapply/main.c $(LIBS)

$(BINDIR)/nodeseat: cmd/nodeseat/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/nodeseat/main.c $(LIBS)

$(BINDIR)/racepulse: cmd/racepulse/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/racepulse/main.c $(LIBS)

$(BINDIR)/ledgerout: cmd/ledgerout/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/ledgerout/main.c $(LIBS)

clean:
	rm -rf $(BINDIR)

.PHONY: all clean
