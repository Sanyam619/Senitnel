CC ?= gcc
CFLAGS ?= -O1 -Wall -Wextra

.PHONY: all
all: $(OUTBIN)

$(OUTBIN): $(HOST_SRC)
	$(CC) $(CFLAGS) -o $@ $< -ldl
