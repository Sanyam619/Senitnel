/* journal_reader.c — streaming journal parser + helpers */

#include <string.h>
#include <stdlib.h>
#include "journal.h"
#include "nfsr.h"

uint16_t le16(const uint8_t *p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

uint32_t le32(const uint8_t *p) {
    return (uint32_t)p[0]
         | ((uint32_t)p[1] << 8)
         | ((uint32_t)p[2] << 16)
         | ((uint32_t)p[3] << 24);
}

uint64_t le64(const uint8_t *p) {
    uint64_t v = 0;
    for (int i = 0; i < 8; i++) {
        v |= ((uint64_t)p[i]) << (i * 8);
    }
    return v;
}

static int expect_magic(FILE *fp, const char *magic8) {
    uint8_t buf[8];
    if (fread(buf, 1, 8, fp) != 8) return -1;
    if (memcmp(buf, magic8, 8) != 0) return -2;
    return 0;
}

int journal_open_server(journal_reader_t *r, const char *path, srv_header_t *hdr_out) {
    memset(r, 0, sizeof(*r));
    r->fp = fopen(path, "rb");
    if (!r->fp) return -1;

    if (expect_magic(r->fp, NFSR_SRV_MAGIC) != 0) {
        fclose(r->fp);
        r->fp = NULL;
        return -2;
    }

    uint8_t rest[32];
    if (fread(rest, 1, 32, r->fp) != 32) {
        fclose(r->fp);
        r->fp = NULL;
        return -3;
    }
    /* version(4) + pad(4) then payload */
    hdr_out->boot_epoch_prev     = le64(rest + 8);
    hdr_out->boot_epoch_curr     = le64(rest + 16);
    hdr_out->grace_window_ms     = le32(rest + 24);
    hdr_out->reclaim_deadline_ms = le32(rest + 28);
    r->body_start = ftell(r->fp);
    return 0;
}

int journal_open_client(journal_reader_t *r, const char *path, cli_header_t *hdr_out) {
    memset(r, 0, sizeof(*r));
    r->fp = fopen(path, "rb");
    if (!r->fp) return -1;

    if (expect_magic(r->fp, NFSR_CLI_MAGIC) != 0) {
        fclose(r->fp);
        r->fp = NULL;
        return -2;
    }

    uint8_t rest[32];
    if (fread(rest, 1, 32, r->fp) != 32) {
        fclose(r->fp);
        r->fp = NULL;
        return -3;
    }
    /* version(4) + pad(4) + client_id[16] + open_owner_seq_start(8) */
    memcpy(hdr_out->client_id, rest + 8, NFSR_CID_LEN);
    hdr_out->open_owner_seq_start = le64(rest + 24);
    r->body_start = ftell(r->fp);
    return 0;
}

int journal_next(journal_reader_t *r, journal_rec_t *rec_out) {
    if (!r->fp) return -1;
    int c = fgetc(r->fp);
    if (c == EOF) return 1;              /* end of stream */
    if (c == 0)  return 1;               /* zero-tag terminator */
    rec_out->tag = (uint8_t)c;

    uint8_t lenbuf[2];
    if (fread(lenbuf, 1, 2, r->fp) != 2) return -2;
    rec_out->length = le16(lenbuf);
    if (rec_out->length > sizeof(rec_out->body)) return -3;

    if (rec_out->length > 0) {
        if (fread(rec_out->body, 1, rec_out->length, r->fp) != rec_out->length) {
            return -4;
        }
    }
    return 0;
}

void journal_close(journal_reader_t *r) {
    if (r->fp) {
        fclose(r->fp);
        r->fp = NULL;
    }
}

int copy_intent_load(const char *path, copy_intent_t *out) {
    FILE *fp = fopen(path, "rb");
    if (!fp) return -1;
    uint8_t buf[NFSR_COPY_REC_LEN];
    size_t n = fread(buf, 1, NFSR_COPY_REC_LEN, fp);
    fclose(fp);
    if (n != NFSR_COPY_REC_LEN) return -2;
    if (memcmp(buf, NFSR_COPY_MAGIC, 8) != 0) return -3;

    memcpy(out->source_fh,      buf + 16, NFSR_FH_LEN);
    memcpy(out->dest_fh,        buf + 32, NFSR_FH_LEN);
    out->session_id     = le64(buf + 48);
    out->total_bytes    = le64(buf + 56);
    out->bytes_flushed  = le64(buf + 64);
    memcpy(out->write_verifier, buf + 72, NFSR_VERIFIER_LEN);
    out->committed_flag = buf[80];
    /* buf[81..87] are pad */
    out->issue_ts_ms    = le64(buf + 88);
    return 0;
}
