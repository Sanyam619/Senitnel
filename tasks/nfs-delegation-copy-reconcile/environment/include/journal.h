/* journal.h — parsed record structures and the streaming reader API */
#ifndef NFSR_JOURNAL_H
#define NFSR_JOURNAL_H

#include <stdint.h>
#include <stdio.h>
#include "nfsr.h"

typedef struct {
    uint64_t boot_epoch_prev;
    uint64_t boot_epoch_curr;
    uint32_t grace_window_ms;
    uint32_t reclaim_deadline_ms;
} srv_header_t;

typedef struct {
    uint8_t client_id[NFSR_CID_LEN];
    uint64_t open_owner_seq_start;
} cli_header_t;

typedef struct {
    uint8_t  tag;
    uint16_t length;
    /* Body payload copied into a bounded buffer. */
    uint8_t  body[256];
} journal_rec_t;

/* Copy intent record fully parsed. */
typedef struct {
    uint8_t  source_fh[NFSR_FH_LEN];
    uint8_t  dest_fh[NFSR_FH_LEN];
    uint64_t session_id;
    uint64_t total_bytes;
    uint64_t bytes_flushed;
    uint8_t  write_verifier[NFSR_VERIFIER_LEN];
    uint8_t  committed_flag;
    uint64_t issue_ts_ms;
} copy_intent_t;

/* Streaming journal reader. Owns the FILE* pointer. */
typedef struct {
    FILE *fp;
    long body_start;
} journal_reader_t;

int journal_open_server(journal_reader_t *r, const char *path, srv_header_t *hdr_out);
int journal_open_client(journal_reader_t *r, const char *path, cli_header_t *hdr_out);
int journal_next(journal_reader_t *r, journal_rec_t *rec_out);
void journal_close(journal_reader_t *r);

int copy_intent_load(const char *path, copy_intent_t *out);

/* Little-endian scalar helpers. */
uint16_t le16(const uint8_t *p);
uint32_t le32(const uint8_t *p);
uint64_t le64(const uint8_t *p);

#endif /* NFSR_JOURNAL_H */
