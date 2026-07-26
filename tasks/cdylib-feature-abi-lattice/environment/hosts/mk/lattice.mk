CC ?= gcc
CFLAGS ?= -O1 -Wall -Wextra
LDFLAGS ?=

# LIBDIR, INCLUDEDIR, SONAME, MODE, OUTBIN set by abi_probe.

.PHONY: all
all: $(OUTBIN)

$(OUTBIN): $(HOST_SRC)
	$(CC) $(CFLAGS) -I$(INCLUDEDIR) -o $@ $< $(LDFLAGS)
