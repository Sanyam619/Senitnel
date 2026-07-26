#include "gate.h"
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>

static void slot_dir(void) {
    mkdir("/tmp/edge_slots", 0755);
}

static void slot_path(char *buf, size_t n, const char *id, char which) {
    snprintf(buf, n, "/tmp/edge_slots/%s.%c", id, which);
}

int slot_write_a(const char *id, const struct slot_a *s) {
    char p[256];
    slot_dir();
    slot_path(p, sizeof(p), id, 'a');
    FILE *fp = fopen(p, "w");
    if (!fp) {
        return -1;
    }
    fprintf(fp, "%d %u\n", s->ok, s->bound_gen);
    fclose(fp);
    return 0;
}

int slot_write_b(const char *id, const struct slot_b *s) {
    char p[256];
    slot_dir();
    slot_path(p, sizeof(p), id, 'b');
    FILE *fp = fopen(p, "w");
    if (!fp) {
        return -1;
    }
    fprintf(fp, "%d %d\n", s->ok, s->used_restore);
    fclose(fp);
    return 0;
}

int slot_write_c(const char *id, const struct slot_c *s) {
    char p[256];
    slot_dir();
    slot_path(p, sizeof(p), id, 'c');
    FILE *fp = fopen(p, "w");
    if (!fp) {
        return -1;
    }
    fprintf(fp, "%d %d\n", s->ok, s->stale);
    fclose(fp);
    return 0;
}

int slot_read_a(const char *id, struct slot_a *s) {
    char p[256];
    slot_path(p, sizeof(p), id, 'a');
    FILE *fp = fopen(p, "r");
    if (!fp) {
        return -1;
    }
    if (fscanf(fp, "%d %u", &s->ok, &s->bound_gen) != 2) {
        fclose(fp);
        return -1;
    }
    fclose(fp);
    return 0;
}

int slot_read_b(const char *id, struct slot_b *s) {
    char p[256];
    slot_path(p, sizeof(p), id, 'b');
    FILE *fp = fopen(p, "r");
    if (!fp) {
        return -1;
    }
    if (fscanf(fp, "%d %d", &s->ok, &s->used_restore) != 2) {
        fclose(fp);
        return -1;
    }
    fclose(fp);
    return 0;
}

int slot_read_c(const char *id, struct slot_c *s) {
    char p[256];
    slot_path(p, sizeof(p), id, 'c');
    FILE *fp = fopen(p, "r");
    if (!fp) {
        return -1;
    }
    if (fscanf(fp, "%d %d", &s->ok, &s->stale) != 2) {
        fclose(fp);
        return -1;
    }
    fclose(fp);
    return 0;
}
