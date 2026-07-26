CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -I/opt/abdev/include -I/opt/abdev/lib
LDFLAGS = -lz -lcrypto -lssl

LIB_SRCS = lib/p4_open.c lib/q1_walk.c lib/r7_probe.c lib/step_a_counters.c
LIB_OBJS = $(LIB_SRCS:.c=.o)
TOOLS = bin/slotstat bin/bootsim bin/recover

.PHONY: all clean

all: $(TOOLS) lib/libab.a

lib/libab.a: $(LIB_OBJS)
	mkdir -p lib
	ar rcs $@ $(LIB_OBJS)

bin:
	mkdir -p bin

bin/slotstat: bin lib/libab.a tools/slotstat.c
	$(CC) $(CFLAGS) -o $@ tools/slotstat.c lib/libab.a $(LDFLAGS)

bin/bootsim: bin lib/libab.a tools/bootsim.c
	$(CC) $(CFLAGS) -o $@ tools/bootsim.c lib/libab.a $(LDFLAGS)

bin/recover: bin lib/libab.a tools/recover.c lib/m3_apply.o lib/ab_policy.o
	$(CC) $(CFLAGS) -o $@ tools/recover.c lib/m3_apply.o lib/ab_policy.o lib/libab.a $(LDFLAGS)

lib/m3_apply.o: lib/m3_apply.c
	$(CC) $(CFLAGS) -c -o $@ lib/m3_apply.c

lib/ab_policy.o: lib/ab_policy.c
	$(CC) $(CFLAGS) -c -o $@ lib/ab_policy.c

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f lib/*.o tools/*.o bin/* lib/libab.a
