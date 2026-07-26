CC ?= gcc
CFLAGS ?= -O2 -fPIC -I. -Iinclude
LDFLAGS ?= -shared

OBJS = fold_w.o score_u.o decoy_fold.o

all: libkern.so

libkern.so: $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) libkern.so

.PHONY: all clean
