CC ?= gcc
CFLAGS ?= -O2 -fPIC -Wall -Wextra
PREFIX ?= /app
SRC ?= /app

.PHONY: all install clean lib

all: lib
	cd $(SRC) && CGO_ENABLED=1 go build -trimpath -o $(PREFIX)/bin/matfan ./cmd/matfan
	cd $(SRC) && CGO_ENABLED=0 go build -trimpath -o $(PREFIX)/bin/dmhealth ./cmd/dmhealth

lib:
	mkdir -p $(PREFIX)/lib $(PREFIX)/bin
	$(CC) $(CFLAGS) -shared -o $(PREFIX)/lib/libioctl_a.so $(SRC)/c/ioctl_a.c
	$(CC) $(CFLAGS) -shared -o $(PREFIX)/lib/libioctl_b.so $(SRC)/c/ioctl_b.c

install: all

clean:
	rm -f $(PREFIX)/bin/matfan $(PREFIX)/bin/dmhealth
	rm -f $(PREFIX)/lib/libioctl_a.so $(PREFIX)/lib/libioctl_b.so
