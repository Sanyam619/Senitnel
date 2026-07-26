CC = gcc
CFLAGS = -std=c11 -Wall -Wextra -O2 -Iinclude

SRCS = \
	src/host/main.c \
	src/host/io.c \
	src/host/report.c \
	src/tier_a/op_alpha.c \
	src/tier_a/scan_profile.c \
	src/tier_b/op_beta.c \
	src/tier_b/scan_rebind.c \
	src/tier_c/op_gamma.c \
	src/tier_c/scan_gate.c \
	src/util/clamp.c \
	src/util/id_eq.c

OBJS = $(SRCS:.c=.o)
BIN = bin/warmup

.PHONY: all clean

all: $(BIN)

$(BIN): $(OBJS)
	mkdir -p bin
	$(CC) $(CFLAGS) -o $@ $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(BIN)
