#ifndef FRAME_H
#define FRAME_H

/* Parsed input row for a single framed record. */
struct row_q {
    const char *leaf;
    const char *parent;
    const char *anchor;
    const char *sig;
    long gen;
};

/* Result slot populated by the framing pass. */
struct slot_q {
    int tip_ok;
    int sig_ok;
    long gen;
};

#endif /* FRAME_H */
