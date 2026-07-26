/* nfsr.h — common constants for the NFSv4.2 reconciliation rig */
#ifndef NFSR_H
#define NFSR_H

#include <stdint.h>
#include <stddef.h>

#define NFSR_FH_LEN            16
#define NFSR_CID_LEN           16
#define NFSR_OWNER_LEN         16
#define NFSR_VERIFIER_LEN      8

#define NFSR_SRV_MAGIC         "NFSRSVR\0"
#define NFSR_CLI_MAGIC         "NFSRCLI\0"
#define NFSR_COPY_MAGIC        "NFSRCPY\0"

#define NFSR_SRV_HDR_LEN       40
#define NFSR_CLI_HDR_LEN       40
#define NFSR_COPY_REC_LEN      96

/* Server record tags. */
#define TAG_RECLAIM_OPEN       0x01
#define TAG_RECLAIM_DELEG_WR   0x02
#define TAG_RECLAIM_DELEG_RD   0x03
#define TAG_COMMIT_SEAL        0x04
#define TAG_NAMESPACE_OP       0x05
#define TAG_COPY_SESSION       0x06

/* Client record tags. */
#define TAG_OPEN               0x11
#define TAG_DELEGATION_HELD   0x12
#define TAG_RENAME             0x13
#define TAG_COPY_ISSUE         0x14
#define TAG_SEQ_TICK           0x15

/* Delegation type flag. */
#define DELEG_TYPE_READ        0
#define DELEG_TYPE_WRITE       1

/* Namespace op codes. */
#define NS_OP_RENAME           1
#define NS_OP_UNLINK           2

/* Copy session states. */
#define COPY_STATE_INTENT      0
#define COPY_STATE_IN_FLIGHT   1
#define COPY_STATE_COMMIT_PEND 2

#endif /* NFSR_H */
