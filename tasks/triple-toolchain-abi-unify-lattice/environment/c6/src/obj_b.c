#include "obj_api.h"

/* Secondary OBJECT unit — keeps CMake OBJECT lane non-trivial. */
unsigned obj_aux_tag(void) {
    return 0xC600u;
}
