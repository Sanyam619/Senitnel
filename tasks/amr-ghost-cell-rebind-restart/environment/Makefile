CC = gcc
CFLAGS = -std=c11 -Wall -Wextra -O2 -Iinclude
LDFLAGS = -lm

SRCS = \
	src/main.c \
	src/hydro/step.c \
	src/hydro/flux.c \
	src/mesh/block_tree.c \
	src/mesh/refine_policy.c \
	src/mesh/mesh_adj.c \
	src/mesh/mesh_coupling.c \
	src/forge/forge_exec.c \
	src/forge/forge_stage.c \
	src/forge/checkpoint_io.c \
	src/ledger/ledger_row.c \
	src/ledger/policy_merge.c \
	src/ledger/catalog_scan.c \
	src/couple/face_pack.c \
	src/couple/halo_fill.c \
	src/couple/residual_bind.c \
	src/couple/stencil_probe.c \
	src/util/crc32.c \
	src/util/json_emit.c

OBJS = $(SRCS:.c=.o)
TARGET = amr_hydro

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

src/%.o: src/%.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(TARGET)
