#ifndef WIRE_H
#define WIRE_H

/* Field keys used by the on-wire record encoding. */
#define WIRE_KEY_LEAF   "leaf"
#define WIRE_KEY_PARENT "parent"
#define WIRE_KEY_SIG    "sig"
#define WIRE_KEY_GEN    "gen"

/* Upper bound on a single record payload in bytes. */
#define WIRE_MAX 8192

#endif /* WIRE_H */
