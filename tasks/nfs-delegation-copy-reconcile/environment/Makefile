CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -I/app/include
LDFLAGS =

LIB_SRCS = lib/journal_reader.c lib/fh_util.c lib/crc32.c lib/state_graph.c
LIB_OBJS = $(LIB_SRCS:.c=.o)
INSPECT_SRCS = tools/inspect.c
INSPECT_OBJS = $(INSPECT_SRCS:.c=.o)

.PHONY: all clean reconcile

all: bin/nfsr-inspect lib/libnfsr.a

bin:
	mkdir -p bin

lib/libnfsr.a: $(LIB_OBJS)
	ar rcs $@ $(LIB_OBJS)

bin/nfsr-inspect: bin $(INSPECT_OBJS) lib/libnfsr.a
	$(CC) $(CFLAGS) -o $@ $(INSPECT_OBJS) lib/libnfsr.a $(LDFLAGS)

# The reconciler is authored by the solver as tools/reconcile.c.
# This target builds it once the source is dropped in.
bin/nfsr-reconcile: bin tools/reconcile.c lib/libnfsr.a
	$(CC) $(CFLAGS) -o $@ tools/reconcile.c lib/libnfsr.a $(LDFLAGS)

reconcile: bin/nfsr-reconcile

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f lib/*.o tools/*.o bin/nfsr-inspect bin/nfsr-reconcile lib/libnfsr.a
