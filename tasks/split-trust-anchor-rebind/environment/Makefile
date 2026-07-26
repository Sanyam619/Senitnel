CC = gcc
CFLAGS = -std=c11 -Wall -Wextra -O2 -Iinclude
SRCS = \
	src/main.c \
	src/vault/load_store.c \
	src/vault/op_a.c \
	src/vault/scan_roots.c \
	src/pinset/load_pins.c \
	src/pinset/op_b.c \
	src/pinset/probe_hot.c \
	src/capdec/decode_tok.c \
	src/capdec/op_c.c \
	src/capdec/cache_view.c \
	src/gate/slot_io.c \
	src/gate/assemble_x.c \
	src/gate/assemble_y.c \
	src/reload/epoch_read.c \
	src/ops/apply_snap.c \
	src/health/surf_tls.c \
	src/util/json_out.c \
	src/util/hexlib.c

OBJS = $(SRCS:.c=.o)
BIN = bin/edgegate

.PHONY: all clean

all: $(BIN)

$(BIN): $(OBJS)
	mkdir -p bin
	$(CC) $(CFLAGS) -o $@ $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(BIN)
