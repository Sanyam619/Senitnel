#ifndef SCENARIO_H
#define SCENARIO_H

#include <stddef.h>

#define SCENARIO_LABEL_MAX 32
#define LAW_STR_MAX 96

typedef struct scenario {
    char label[SCENARIO_LABEL_MAX];
    int nx;
    int ny;
    char kx_law[LAW_STR_MAX];
    char ky_law[LAW_STR_MAX];
    char rhs_law[LAW_STR_MAX];
    int budget;
} scenario_t;

int scenario_load(const char *path, scenario_t *out);

/* Evaluate the coefficient at face-midpoint (x, y). */
double coeff_kx(const scenario_t *s, double x, double y);
double coeff_ky(const scenario_t *s, double x, double y);

/* Evaluate the right-hand-side source at node (x, y). */
double rhs_eval(const scenario_t *s, double x, double y);

#endif /* SCENARIO_H */
