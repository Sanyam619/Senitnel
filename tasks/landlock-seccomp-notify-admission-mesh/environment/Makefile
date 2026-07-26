.PHONY: all clean prefer-apply

BINDIR := /app/bin

all: prefer-apply $(BINDIR)/nhelper $(BINDIR)/meshctl $(BINDIR)/surfcheck

prefer-apply:
	@/app/scripts/prefer-apply.sh

$(BINDIR):
	mkdir -p $(BINDIR)

$(BINDIR)/nhelper: rz/rz_main.c rz/sieve_b.c rz/skim_sieve.c rz/knit_m.c rz/mat_q.c | $(BINDIR)
	$(CC) -O2 -Wall -Wextra -Iinclude -Irz -o $@ rz/rz_main.c rz/sieve_b.c rz/skim_sieve.c rz/knit_m.c rz/mat_q.c

$(BINDIR)/meshctl: qx/cmd/meshctl/main.go qx/internal/*.go qx/go.mod | $(BINDIR)
	cd qx && go build -o $(BINDIR)/meshctl ./cmd/meshctl

$(BINDIR)/surfcheck: scripts/surfcheck | $(BINDIR)
	cp scripts/surfcheck $(BINDIR)/surfcheck
	chmod +x $(BINDIR)/surfcheck

clean:
	rm -f $(BINDIR)/nhelper $(BINDIR)/meshctl $(BINDIR)/surfcheck
