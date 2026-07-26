#include "obj_api.h"
#include "slot_abi.h"

unsigned obj_abi_stamp(void) {
    return (unsigned)SLOT_ABI_STAMP;
}

unsigned obj_pack_width(void) {
#ifdef PACK_WIDTH
    return (unsigned)PACK_WIDTH;
#else
    return (unsigned)SLOT_PACK_WIDTH;
#endif
}
