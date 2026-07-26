# Host build. Includes knit_xv_a for CC/TLS/PIE fragments.
ROOT ?= /app
BUILD ?= $(ROOT)/build/h4
PROFILE ?= target
LANE ?= musl

include $(ROOT)/h4/mk/knit_xv_a.mk

$(eval $(call knit_xv_a,$(PROFILE),$(LANE)))

# Stamp-only cutover: knit_xv_a owns CC/TLS/PIE values written to host.flags
# for the probe report. The in-tree host still compiles with the local loader
# toolchain so glibc-linked plugins can dlopen during matrix observation.
REAL_CC ?= gcc
CFLAGS ?= -I$(ROOT)/include -Wall -O2 -ftls-model=$(XV_TLS) $(XV_PIE)
LDFLAGS ?= $(XV_PIE) -ldl

.PHONY: all clean stamp

all: $(BUILD)/gateway_host $(BUILD)/host.flags

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/host.flags: | $(BUILD)
	@echo "CC=$(XV_CC)" > $@
	@echo "TLS_MODEL=$(XV_TLS)" >> $@
	@echo "PIE=$(XV_PIE)" >> $@
	@echo "LANE=$(LANE)" >> $@
	@echo "PROFILE=$(PROFILE)" >> $@

$(BUILD)/main.o: $(ROOT)/h4/src/main.c | $(BUILD)
	$(REAL_CC) $(CFLAGS) -DXV_TLS_STR=\"$(XV_TLS)\" -c -o $@ $<

$(BUILD)/loader.o: $(ROOT)/h4/src/loader.c | $(BUILD)
	$(REAL_CC) $(CFLAGS) -c -o $@ $<

$(BUILD)/gateway_host: $(BUILD)/main.o $(BUILD)/loader.o $(BUILD)/host.flags
	$(REAL_CC) -o $@ $(BUILD)/main.o $(BUILD)/loader.o $(LDFLAGS)

stamp: $(BUILD)/host.flags

clean:
	rm -rf $(BUILD)
