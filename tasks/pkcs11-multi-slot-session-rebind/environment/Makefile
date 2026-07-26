JAVAC ?= javac
JAVA ?= java
JAR ?= jar
CLASSES := classes

LIB_SRC := $(wildcard lib/*.java)
WIRE_SRC := $(wildcard flux/*.java)
HOLD_SRC := $(wildcard nest/*.java)
STAMP_SRC := $(wildcard forge/*.java)
CMD_SRC := $(wildcard cmd/*/*.java)
ALL_SRC := $(LIB_SRC) $(WIRE_SRC) $(HOLD_SRC) $(STAMP_SRC) $(CMD_SRC)

BIN_DIR := bin
TOOLS := findscan slotprobe wireapply holdrun emitout authcheck sealgen
GATE_JAR := /opt/pk11/lib/gate.jar
OPS_JAR := /opt/pk11/lib/ops.jar
# Sealed ops first so rebuildable classes cannot shadow engine/seal implementations.
RUNTIME_CP = $(OPS_JAR):$(GATE_JAR):/opt/pk11/classes
LOCAL_CP = $(OPS_JAR):$(GATE_JAR):$(CURDIR)/$(CLASSES)

.PHONY: all clean install seal-gate seal-ops

all: $(CLASSES)/.stamp $(addprefix $(BIN_DIR)/,$(TOOLS))

$(CLASSES)/.stamp: $(ALL_SRC)
	mkdir -p $(CLASSES)
	$(JAVAC) -d $(CLASSES) $(ALL_SRC)
	touch $@

define WRITE_TOOL
	mkdir -p $(BIN_DIR)
	printf '%s\n' '#!/bin/sh' \
	  'if [ -f "$(OPS_JAR)" ]; then CP="$(LOCAL_CP)"; else CP="$(CURDIR)/$(CLASSES)"; fi' \
	  'exec $(JAVA) -cp "$$CP" $(1).Main "$$@"' > $(BIN_DIR)/$(1)
	chmod +x $(BIN_DIR)/$(1)
endef

$(BIN_DIR)/findscan: $(CLASSES)/.stamp
	$(call WRITE_TOOL,findscan)

$(BIN_DIR)/slotprobe: $(CLASSES)/.stamp
	$(call WRITE_TOOL,slotprobe)

$(BIN_DIR)/wireapply: $(CLASSES)/.stamp
	$(call WRITE_TOOL,wireapply)

$(BIN_DIR)/holdrun: $(CLASSES)/.stamp
	$(call WRITE_TOOL,holdrun)

$(BIN_DIR)/emitout: $(CLASSES)/.stamp
	$(call WRITE_TOOL,emitout)

$(BIN_DIR)/authcheck: $(CLASSES)/.stamp
	$(call WRITE_TOOL,authcheck)

$(BIN_DIR)/sealgen: $(CLASSES)/.stamp
	$(call WRITE_TOOL,sealgen)

# Seal engines, seal math, and cutover CLI entrypoints so preference sheets
# cannot be bypassed by rewriting thin Main wrappers under /app/cmd.
seal-ops: $(CLASSES)/.stamp
	mkdir -p /opt/pk11/lib
	cd $(CLASSES) && $(JAR) cf $(OPS_JAR) \
	  flux/OpA.class nest/OpB.class forge/OpC.class \
	  lib/SealUtil.class lib/Journal.class \
	  wireapply/Main.class holdrun/Main.class emitout/Main.class sealgen/Main.class
	rm -f $(CLASSES)/flux/OpA.class $(CLASSES)/nest/OpB.class $(CLASSES)/forge/OpC.class \
	  $(CLASSES)/lib/SealUtil.class $(CLASSES)/lib/Journal.class \
	  $(CLASSES)/wireapply/Main.class $(CLASSES)/holdrun/Main.class \
	  $(CLASSES)/emitout/Main.class $(CLASSES)/sealgen/Main.class
	rm -f /app/flux/OpA.java /app/nest/OpB.java /app/forge/OpC.java \
	  /app/lib/SealUtil.java /app/lib/Journal.java \
	  /app/cmd/wireapply/Main.java /app/cmd/holdrun/Main.java \
	  /app/cmd/emitout/Main.java /app/cmd/sealgen/Main.java 2>/dev/null || true
	rm -f flux/OpA.java nest/OpB.java forge/OpC.java lib/SealUtil.java lib/Journal.java \
	  cmd/wireapply/Main.java cmd/holdrun/Main.java cmd/emitout/Main.java cmd/sealgen/Main.java \
	  2>/dev/null || true

seal-gate: $(CLASSES)/.stamp
	mkdir -p /opt/pk11/lib
	cd $(CLASSES) && $(JAR) cf $(GATE_JAR) lib/Vx.class
	rm -f $(CLASSES)/lib/Vx.class /app/lib/Vx.java 2>/dev/null || true
	rm -f lib/Vx.java 2>/dev/null || true

install: all
	mkdir -p /opt/pk11/bin /opt/pk11/classes /opt/pk11/config /opt/pk11/lib
	cp -a $(CLASSES)/. /opt/pk11/classes/
	rm -f /opt/pk11/classes/lib/Vx.class \
	  /opt/pk11/classes/flux/OpA.class /opt/pk11/classes/nest/OpB.class \
	  /opt/pk11/classes/forge/OpC.class \
	  /opt/pk11/classes/lib/SealUtil.class /opt/pk11/classes/lib/Journal.class \
	  /opt/pk11/classes/wireapply/Main.class /opt/pk11/classes/holdrun/Main.class \
	  /opt/pk11/classes/emitout/Main.class /opt/pk11/classes/sealgen/Main.class
	for t in $(TOOLS); do \
	  printf '%s\n' '#!/bin/sh' \
	    "exec $(JAVA) -cp $(RUNTIME_CP) $${t}.Main \"\$$@\"" > /opt/pk11/bin/$$t; \
	  chmod +x /opt/pk11/bin/$$t; \
	done

clean:
	rm -rf $(CLASSES) $(BIN_DIR)
