# JNI shared library for the bridge unit.
CC ?= gcc
CFLAGS ?= -fPIC -O2 -I$(JAVA_HOME)/include -I$(JAVA_HOME)/include/linux -I$(JAVA_HOME)/include/darwin
LDFLAGS ?= -shared

all: libhelixhook.so

libhelixhook.so: hook.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ hook.c

clean:
	rm -f libhelixhook.so

.PHONY: all clean
