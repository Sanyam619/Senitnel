#ifndef IO_H
#define IO_H

#include "level.h"
#include "scenario.h"

typedef struct scenario_result {
    char label[SCENARIO_LABEL_MAX];
    int iterations;
    double residual;
    int budget;
} scenario_result_t;

int trace_emit(const char *label, const double *history, int count);
int field_emit(const char *label, const level_t *lvl);
int json_emit_report(const char *out_path, const scenario_result_t *results,
                     int count, int all_within_budget);

#endif /* IO_H */
