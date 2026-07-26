CC = gcc
CFLAGS = -Wall -Wextra -O2 -I. -Iinclude
LIBS = lib/state_io.c lib/path_util.c lib/tier_policy.c ring/apply_ring_a.c ring/legacy_ring.c gate/cycle_gate_b.c gate/probe_gate.c roll/emit_roll_c.c

BINDIR = bin

all: $(BINDIR)/topsurf $(BINDIR)/nsprobe $(BINDIR)/ringapply $(BINDIR)/gatecycle $(BINDIR)/racepulse $(BINDIR)/ledgerout $(BINDIR)/unseat $(BINDIR)/remark

$(BINDIR):
	mkdir -p $(BINDIR)

$(BINDIR)/topsurf: cmd/topsurf/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/topsurf/main.c $(LIBS)

$(BINDIR)/nsprobe: cmd/nsprobe/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/nsprobe/main.c $(LIBS)

$(BINDIR)/ringapply: cmd/ringapply/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/ringapply/main.c $(LIBS)

$(BINDIR)/gatecycle: cmd/gatecycle/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/gatecycle/main.c $(LIBS)

$(BINDIR)/racepulse: cmd/racepulse/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/racepulse/main.c $(LIBS)

$(BINDIR)/ledgerout: cmd/ledgerout/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/ledgerout/main.c $(LIBS)

$(BINDIR)/unseat: cmd/unseat/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/unseat/main.c $(LIBS)

$(BINDIR)/remark: cmd/remark/main.c $(LIBS) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ cmd/remark/main.c $(LIBS)

clean:
	rm -rf $(BINDIR)

.PHONY: all clean
