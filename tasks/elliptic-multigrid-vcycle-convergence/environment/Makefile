CC = gcc
CFLAGS = -std=c11 -Wall -Wextra -O2 -Iinclude
LDFLAGS = -lm

SRCS = \
	src/main.c \
	src/grid/grid_alloc.c \
	src/grid/stencil_apply.c \
	src/grid/residual.c \
	src/operators/fine_assembly.c \
	src/operators/coarse_assembly.c \
	src/levels/restrict_prolong.c \
	src/levels/level_policy.c \
	src/relaxation/weighted_jacobi.c \
	src/vcycle/vcycle.c \
	src/vcycle/coarse_solve.c \
	src/scenario/scenario_load.c \
	src/scenario/coeff_laws.c \
	src/scenario/rhs_laws.c \
	src/io/json_emit.c \
	src/io/trace_emit.c \
	src/io/field_emit.c

OBJS = $(SRCS:.c=.o)
TARGET = elliptic_mg

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

src/%.o: src/%.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(TARGET)
