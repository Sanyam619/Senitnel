/* inspect.c — read-only walker over an episode directory.
 * Usage: nfsr-inspect <episode-dir>
 * Prints one line per record in each journal file for eyeballing. */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/stat.h>
#include "journal.h"
#include "fh_util.h"
#include "nfsr.h"

static void print_fh(const char *label, const uint8_t *fh) {
    char hex[33];
    fh_to_hex(fh, hex);
    printf(" %s=%s", label, hex);
}

static void dump_server(const char *path) {
    srv_header_t hdr;
    journal_reader_t rd;
    if (journal_open_server(&rd, path, &hdr) != 0) {
        fprintf(stderr, "inspect: cannot open server log %s\n", path);
        return;
    }
    printf("== server_reclaim.log ==\n");
    printf("boot_prev=%llu boot_curr=%llu grace_ms=%u deadline_ms=%u\n",
           (unsigned long long)hdr.boot_epoch_prev,
           (unsigned long long)hdr.boot_epoch_curr,
           hdr.grace_window_ms, hdr.reclaim_deadline_ms);

    journal_rec_t rec;
    int rc;
    int idx = 0;
    while ((rc = journal_next(&rd, &rec)) == 0) {
        printf("[%03d] tag=0x%02x len=%u", idx++, rec.tag, rec.length);
        switch (rec.tag) {
            case TAG_RECLAIM_OPEN:
                if (rec.length >= 56) {
                    print_fh("cid",   rec.body);
                    print_fh("owner", rec.body + 16);
                    printf(" seq=%llu", (unsigned long long)le64(rec.body + 32));
                    print_fh("fh",    rec.body + 40);
                }
                break;
            case TAG_RECLAIM_DELEG_WR:
            case TAG_RECLAIM_DELEG_RD:
                if (rec.length >= 48) {
                    print_fh("cid",  rec.body);
                    printf(" seq=%llu", (unsigned long long)le64(rec.body + 16));
                    print_fh("fh",   rec.body + 24);
                    printf(" epoch=%llu",
                           (unsigned long long)le64(rec.body + 40));
                }
                break;
            case TAG_COMMIT_SEAL:
                if (rec.length >= 24) {
                    printf(" seq=%llu", (unsigned long long)le64(rec.body));
                    printf(" ver=");
                    for (int i = 0; i < 8; i++) printf("%02x", rec.body[8 + i]);
                    printf(" dur=%llu", (unsigned long long)le64(rec.body + 16));
                }
                break;
            case TAG_NAMESPACE_OP:
                if (rec.length >= 41) {
                    printf(" op=%u", rec.body[0]);
                    print_fh("src", rec.body + 1);
                    print_fh("dst", rec.body + 17);
                    printf(" ts=%llu", (unsigned long long)le64(rec.body + 33));
                }
                break;
            case TAG_COPY_SESSION:
                if (rec.length >= 41) {
                    print_fh("src", rec.body);
                    print_fh("dst", rec.body + 16);
                    printf(" session=%llu state=%u",
                           (unsigned long long)le64(rec.body + 32),
                           rec.body[40]);
                }
                break;
            default:
                break;
        }
        printf("\n");
    }
    if (rc < 0) {
        fprintf(stderr, "inspect: server log parse error (rc=%d)\n", rc);
    }
    journal_close(&rd);
}

static void dump_client(const char *path, const char *label) {
    cli_header_t hdr;
    journal_reader_t rd;
    if (journal_open_client(&rd, path, &hdr) != 0) {
        fprintf(stderr, "inspect: cannot open client log %s\n", path);
        return;
    }
    char cid_hex[33];
    fh_to_hex(hdr.client_id, cid_hex);
    printf("== %s ==\n", label);
    printf("client_id=%s owner_seq_start=%llu\n",
           cid_hex, (unsigned long long)hdr.open_owner_seq_start);

    journal_rec_t rec;
    int rc;
    int idx = 0;
    while ((rc = journal_next(&rd, &rec)) == 0) {
        printf("[%03d] tag=0x%02x len=%u", idx++, rec.tag, rec.length);
        switch (rec.tag) {
            case TAG_OPEN:
                if (rec.length >= 36) {
                    printf(" owner_seq=%llu", (unsigned long long)le64(rec.body));
                    print_fh("fh", rec.body + 8);
                    printf(" mode=%u ts=%llu", le32(rec.body + 24),
                           (unsigned long long)le64(rec.body + 28));
                }
                break;
            case TAG_DELEGATION_HELD:
                if (rec.length >= 33) {
                    printf(" seq=%llu", (unsigned long long)le64(rec.body));
                    print_fh("fh", rec.body + 8);
                    printf(" type=%u epoch=%llu", rec.body[24],
                           (unsigned long long)le64(rec.body + 25));
                }
                break;
            case TAG_RENAME:
                if (rec.length >= 49) {
                    print_fh("src", rec.body);
                    print_fh("dst", rec.body + 16);
                    printf(" seq=%llu ts=%llu backed=%u",
                           (unsigned long long)le64(rec.body + 32),
                           (unsigned long long)le64(rec.body + 40),
                           rec.body[48]);
                }
                break;
            case TAG_COPY_ISSUE:
                if (rec.length >= 56) {
                    print_fh("src", rec.body);
                    print_fh("dst", rec.body + 16);
                    printf(" session=%llu off=%llu len=%llu",
                           (unsigned long long)le64(rec.body + 32),
                           (unsigned long long)le64(rec.body + 40),
                           (unsigned long long)le64(rec.body + 48));
                }
                break;
            case TAG_SEQ_TICK:
                if (rec.length >= 8) {
                    printf(" new_seq=%llu", (unsigned long long)le64(rec.body));
                }
                break;
            default:
                break;
        }
        printf("\n");
    }
    if (rc < 0) {
        fprintf(stderr, "inspect: client log parse error (rc=%d)\n", rc);
    }
    journal_close(&rd);
}

static void dump_copy_intent(const char *path) {
    copy_intent_t ci;
    if (copy_intent_load(path, &ci) != 0) {
        fprintf(stderr, "inspect: cannot open copy intent %s\n", path);
        return;
    }
    char src[33], dst[33];
    fh_to_hex(ci.source_fh, src);
    fh_to_hex(ci.dest_fh, dst);
    printf("== copy_intent.rec ==\n");
    printf("src=%s dst=%s session=%llu total=%llu flushed=%llu committed=%u ts=%llu ver=",
           src, dst,
           (unsigned long long)ci.session_id,
           (unsigned long long)ci.total_bytes,
           (unsigned long long)ci.bytes_flushed,
           ci.committed_flag,
           (unsigned long long)ci.issue_ts_ms);
    for (int i = 0; i < 8; i++) printf("%02x", ci.write_verifier[i]);
    printf("\n");
}

static void dump_namespace(const char *path) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        fprintf(stderr, "inspect: cannot open namespace %s\n", path);
        return;
    }
    printf("== namespace.snap ==\n");
    char line[512];
    while (fgets(line, sizeof(line), fp)) {
        fputs(line, stdout);
    }
    fclose(fp);
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: nfsr-inspect <episode-dir>\n");
        return 2;
    }
    char path[512];
    struct stat st;
    if (stat(argv[1], &st) != 0 || !S_ISDIR(st.st_mode)) {
        fprintf(stderr, "nfsr-inspect: not a directory: %s\n", argv[1]);
        return 2;
    }

    snprintf(path, sizeof(path), "%s/server_reclaim.log", argv[1]);
    dump_server(path);
    snprintf(path, sizeof(path), "%s/client_a_ops.log", argv[1]);
    dump_client(path, "client_a_ops.log");
    snprintf(path, sizeof(path), "%s/client_b_ops.log", argv[1]);
    dump_client(path, "client_b_ops.log");
    snprintf(path, sizeof(path), "%s/copy_intent.rec", argv[1]);
    dump_copy_intent(path);
    snprintf(path, sizeof(path), "%s/namespace.snap", argv[1]);
    dump_namespace(path);
    return 0;
}
