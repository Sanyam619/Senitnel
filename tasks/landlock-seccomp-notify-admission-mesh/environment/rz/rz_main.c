#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "knit_m.h"
#include "mat_q.h"
#include "sieve_b.h"
#include "skim_sieve.h"
#include "wire.h"

static int hex_nibble(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static int parse_hex(const char *s, unsigned char *out, size_t cap, size_t *n)
{
    size_t len = strlen(s);
    size_t i;
    if (len % 2 != 0 || len / 2 > cap) return -1;
    for (i = 0; i < len; i += 2) {
        int hi = hex_nibble(s[i]);
        int lo = hex_nibble(s[i + 1]);
        if (hi < 0 || lo < 0) return -1;
        out[i / 2] = (unsigned char)((hi << 4) | lo);
    }
    *n = len / 2;
    return 0;
}

static void usage(const char *prog)
{
    fprintf(stderr, "usage: %s decide <bit> <op> <wire>\n", prog);
    fprintf(stderr, "       %s surface <bit> <op> <wire>\n", prog);
    fprintf(stderr, "       %s integ <seed_hex> <epoch> <lane> <strand> <payload_hex> <check>\n", prog);
}

int main(int argc, char **argv)
{
    int bit;
    int out;

    if (argc >= 2 && strcmp(argv[1], "integ") == 0) {
        unsigned char seed[64];
        unsigned char payload[256];
        unsigned char material[64];
        size_t sn = 0, pn = 0;
        unsigned epoch, lane, strand, check;
        if (argc != 8) {
            usage(argv[0]);
            return 2;
        }
        if (parse_hex(argv[2], seed, sizeof seed, &sn) != 0) return 2;
        epoch = (unsigned)strtoul(argv[3], NULL, 10);
        lane = (unsigned)strtoul(argv[4], NULL, 10);
        strand = (unsigned)strtoul(argv[5], NULL, 10);
        if (parse_hex(argv[6], payload, sizeof payload, &pn) != 0) return 2;
        check = (unsigned)strtoul(argv[7], NULL, 10);
        mat_q(seed, sn, epoch, lane, strand, material);
        out = knit_m(payload, pn, material, sn, check);
        printf("%d\n", out);
        return WIRE_OK;
    }

    if (argc != 5) {
        usage(argv[0]);
        return 2;
    }

    bit = atoi(argv[2]);
    if (strcmp(argv[1], "surface") == 0) {
        out = skim_sieve(bit, argv[3], argv[4]);
    } else if (strcmp(argv[1], "decide") == 0) {
        out = sieve_b(bit, argv[3], argv[4]);
    } else {
        usage(argv[0]);
        return 2;
    }

    printf("%d\n", out);
    return WIRE_OK;
}
