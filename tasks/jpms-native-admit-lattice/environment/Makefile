JAVAC ?= javac
JAVA ?= java
JAR ?= jar
CC ?= gcc

CLASSES := classes
JNI_LIB := /opt/desk/lib/libpackjni.so
GATE_JAR := /opt/desk/lib/gate.jar
BIN := /opt/desk/bin

LIB_SRC := $(wildcard lib/*.java)
FLUX_SRC := $(wildcard flux/*.java)
NEST_SRC := $(wildcard nest/*.java)
FORGE_SRC := $(wildcard forge/*.java)
DESK_SRC := $(wildcard desk/*.java)
CMD_SRC := $(wildcard cmd/*/*.java)
GATE_SRC := $(wildcard gate/*.java)

JAVA_SRC := $(LIB_SRC) $(FLUX_SRC) $(NEST_SRC) $(FORGE_SRC) $(DESK_SRC) $(CMD_SRC)

.PHONY: all clean install seal-gate native

all: native $(CLASSES)/.stamp

native: $(JNI_LIB)

$(JNI_LIB): native/knit_xv.c native/skim_xv.c native/desk_jni.c include/knit_xv.h include/desk_native.h
	mkdir -p /opt/desk/lib
	$(CC) -shared -fPIC -O2 \
		-Iinclude -I"$(JAVA_HOME)/include" -I"$(JAVA_HOME)/include/linux" \
		-o $(JNI_LIB) native/knit_xv.c native/skim_xv.c native/desk_jni.c

$(CLASSES)/.stamp: $(JAVA_SRC) $(GATE_SRC)
	mkdir -p $(CLASSES)
	@if [ -n "$(GATE_SRC)" ]; then \
		$(JAVAC) -d $(CLASSES) $(JAVA_SRC) $(GATE_SRC); \
	else \
		$(JAVAC) -cp $(GATE_JAR) -d $(CLASSES) $(JAVA_SRC); \
	fi
	touch $@

seal-gate: $(CLASSES)/.stamp
	mkdir -p /opt/desk/lib
	cd $(CLASSES) && $(JAR) cf $(GATE_JAR) gate/GateSeal.class
	rm -f $(CLASSES)/gate/GateSeal.class
	rm -f gate/GateSeal.java
	rmdir $(CLASSES)/gate 2>/dev/null || true

install: all
	mkdir -p $(BIN) /opt/desk/classes /opt/desk/lib /app/bin
	cp -a $(CLASSES)/. /opt/desk/classes/
	# Never overwrite sealed gate with a workspace GateSeal.class.
	rm -rf /opt/desk/classes/gate
	printf '%s\n' '#!/bin/sh' \
		"exec $(JAVA) -cp $(GATE_JAR):/opt/desk/classes desk.DeskMain \"\$$@\"" \
		> $(BIN)/admitctl
	printf '%s\n' '#!/bin/sh' \
		"exec $(JAVA) -cp $(GATE_JAR):/opt/desk/classes packhold.Main \"\$$@\"" \
		> $(BIN)/packhold
	printf '%s\n' '#!/bin/sh' \
		"exec $(JAVA) -cp $(GATE_JAR):/opt/desk/classes holdrun.Main \"\$$@\"" \
		> $(BIN)/holdrun
	printf '%s\n' '#!/bin/sh' \
		"exec $(JAVA) -cp $(GATE_JAR):/opt/desk/classes emitout.Main \"\$$@\"" \
		> $(BIN)/emitout
	chmod +x $(BIN)/admitctl $(BIN)/packhold $(BIN)/holdrun $(BIN)/emitout
	ln -sfn $(BIN)/admitctl /app/bin/admitctl
	cp -f scripts/surfcheck /app/bin/surfcheck
	chmod +x /app/bin/surfcheck scripts/*.sh

clean:
	rm -rf $(CLASSES)
