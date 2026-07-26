#include "obj_api.h"

/* Companion object kept in the static archive for membership counts. */
unsigned obj_marker(void) {
    return 0xC9u;
}
