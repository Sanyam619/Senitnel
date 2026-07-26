#include "obj_api.h"
#include "slot_vis.h"

#ifndef ARCHIVE_MEMBERS
#define ARCHIVE_MEMBERS 4
#endif

unsigned obj_vis_digest(void) {
    return (unsigned)SLOT_VIS_DIGEST;
}

unsigned obj_bitcode_epoch(void) {
    return (unsigned)SLOT_BITCODE_EPOCH;
}

unsigned obj_archive_members(void) {
    return (unsigned)ARCHIVE_MEMBERS;
}
