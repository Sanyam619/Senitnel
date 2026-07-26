BIN := bin
CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra -Iinclude -Iframe

.PHONY: all clean surface

all: $(BIN)/framectl $(BIN)/polgate $(BIN)/enrollctl surface

$(BIN):
	mkdir -p $(BIN)

$(BIN)/framectl: frame/frame_main.c frame/fold_q.c frame/skim_frame.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ frame/frame_main.c frame/fold_q.c frame/skim_frame.c

$(BIN)/polgate: policy/src/main.rs policy/src/lib.rs policy/src/gate_r.rs policy/src/skim_pol.rs policy/Cargo.toml | $(BIN)
	cargo build --release --manifest-path policy/Cargo.toml
	cp -f policy/target/release/polgate $@

$(BIN)/enrollctl: enroll/cmd/enrollctl/main.go enroll/internal/emit.go enroll/internal/slot_w.go enroll/internal/skim_en.go enroll/go.mod | $(BIN)
	cd enroll && go build -o ../$(BIN)/enrollctl ./cmd/enrollctl

surface: | $(BIN)
	ln -sf ../scripts/surfcheck $(BIN)/surfcheck

clean:
	rm -rf $(BIN) policy/target
