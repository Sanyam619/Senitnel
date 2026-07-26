CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -I/opt/kvfs/include -I/opt/kvfs/lib
LDFLAGS = -lz
RECON_LDFLAGS = -lz -lcrypto -lssl

LIB_SRCS = lib/k9_scan.c lib/m3_apply.c lib/p7_sb.c lib/r2_inode.c lib/u8_crc.c
LIB_OBJS = $(LIB_SRCS:.c=.o)
TOOL_SRCS = tools/volpeek.c
TOOL_OBJS = $(TOOL_SRCS:.c=.o)

.PHONY: all clean

all: bin/volpeek bin/reconcile lib/libkvfs.a

bin:
	mkdir -p bin

bin/reconcile: bin tools/reconcile.c lib/libkvfs.a lib/m3_apply.o
	$(CC) $(CFLAGS) -o $@ tools/reconcile.c lib/m3_apply.o lib/libkvfs.a $(RECON_LDFLAGS)

lib/m3_apply.o: lib/m3_apply.c
	$(CC) $(CFLAGS) -c -o $@ lib/m3_apply.c

lib/libkvfs.a: $(LIB_OBJS)
	ar rcs $@ $(LIB_OBJS)

bin/volpeek: bin $(TOOL_OBJS) lib/libkvfs.a
	$(CC) $(CFLAGS) -o $@ $(TOOL_OBJS) lib/libkvfs.a $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f lib/*.o tools/*.o bin/volpeek bin/reconcile lib/libkvfs.a
