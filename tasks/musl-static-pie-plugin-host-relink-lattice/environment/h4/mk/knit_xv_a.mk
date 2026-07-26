# Emits host CC/LD flag fragments from profile probes during the C host build.
# Usage: $(eval $(call knit_xv_a,<profile>,<lane>))

define knit_xv_a
XV_CC := gcc
XV_TLS := initial-exec
XV_PIE :=
XV_EXTRA := -Wl,-z,relro
XV_RPATH :=
XV_ABI := legacy
ifeq ($(1),musl)
ifeq ($(2),target)
XV_CC := gcc
XV_TLS := initial-exec
XV_PIE :=
XV_EXTRA := -Wl,-z,relro
XV_RPATH := /usr/lib
XV_ABI := legacy
else
XV_CC := gcc
XV_TLS := initial-exec
XV_PIE :=
XV_EXTRA :=
XV_RPATH :=
XV_ABI := legacy
endif
else
ifeq ($(1),builder)
XV_CC := gcc
XV_TLS := initial-exec
XV_PIE :=
XV_EXTRA := -Wl,-z,relro
XV_RPATH := /usr/lib
XV_ABI := builder
else
XV_CC := gcc
XV_TLS := initial-exec
XV_PIE :=
XV_EXTRA := -Wl,-z,relro
XV_RPATH :=
XV_ABI := legacy
endif
endif
endef
