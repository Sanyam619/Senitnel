#include "vcycle.h"
#include "level.h"
#include "grid.h"
#include "scenario.h"
#include "solver_config.h"
#include "io.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Populate the finest-level RHS field from the scenario RHS law. */
static void assemble_rhs(level_t *lvl, const scenario_t *scen) {
    int nx = lvl->dims.nx;
    int ny = lvl->dims.ny;
    double hx = lvl->dims.hx;
    double hy = lvl->dims.hy;
    for (int i = 0; i < nx; i++) {
        double x = i * hx;
        for (int j = 0; j < ny; j++) {
            double y = j * hy;
            int k = grid_index(i, j, ny);
            if (i == 0 || i == nx - 1 || j == 0 || j == ny - 1) {
                lvl->f[k] = 0.0; /* Homogeneous Dirichlet. */
            } else {
                lvl->f[k] = rhs_eval(scen, x, y);
            }
        }
    }
}

static int run_scenario(const char *desc_path, scenario_result_t *out_result) {
    scenario_t scen;
    if (scenario_load(desc_path, &scen) != 0) {
        fprintf(stderr, "failed to load %s\n", desc_path);
        return -1;
    }

    hierarchy_t h;
    if (hierarchy_build(&h, &scen) != 0) {
        fprintf(stderr, "hierarchy build failed for %s\n", scen.label);
        return -1;
    }

    /* Assemble the operator on the finest level, then compute all
     * coarse operators. Populate per-level relaxation weights. */
    fine_operator_assemble(&h.levels[0], &scen);
    for (int L = 1; L < h.num_levels; L++) {
        coarse_operator_assemble(&h.levels[L - 1], &h.levels[L]);
    }
    for (int L = 0; L < h.num_levels; L++) {
        h.levels[L].omega = relax_weight_for(L, &scen);
    }
    if (coarse_solve_prepare(&h.levels[h.num_levels - 1]) != 0) {
        fprintf(stderr, "coarse solve prep failed for %s\n", scen.label);
        hierarchy_free(&h);
        return -1;
    }

    assemble_rhs(&h.levels[0], &scen);

    static double history[MAX_OUTER_ITERATIONS + 2];
    double final_res = 0.0;
    int iters = vcycle_solve(&h, &scen, history, &final_res);

    /* Trace has iters + 1 entries (initial residual + one per V-cycle),
     * but the visible convention is iters entries (residual after each
     * V-cycle). Drop the initial-guess residual before writing. */
    trace_emit(scen.label, &history[1], iters);
    field_emit(scen.label, &h.levels[0]);

    snprintf(out_result->label, sizeof(out_result->label), "%s", scen.label);
    out_result->iterations = iters;
    out_result->residual = final_res;
    out_result->budget = scen.budget;

    hierarchy_free(&h);
    return 0;
}

int main(int argc, char **argv) {
    static const char *DEFAULT_SCENARIOS[] = {
        "/app/data/scenarios/s_iso.desc",
        "/app/data/scenarios/s_aniso.desc",
        "/app/data/scenarios/s_jump.desc",
        "/app/data/scenarios/s_corner.desc",
        "/app/data/scenarios/s_mixed.desc",
    };
    static const int DEFAULT_COUNT =
        (int)(sizeof(DEFAULT_SCENARIOS) / sizeof(DEFAULT_SCENARIOS[0]));

    const char **paths;
    int count;
    if (argc > 1) {
        paths = (const char **)&argv[1];
        count = argc - 1;
    } else {
        paths = DEFAULT_SCENARIOS;
        count = DEFAULT_COUNT;
    }

    scenario_result_t *results = calloc((size_t)count, sizeof(*results));
    if (!results) return 1;

    int all_within = 1;
    for (int i = 0; i < count; i++) {
        if (run_scenario(paths[i], &results[i]) != 0) {
            free(results);
            return 1;
        }
        if (results[i].iterations > results[i].budget ||
            results[i].residual > RESIDUAL_TARGET) {
            all_within = 0;
        }
    }

    json_emit_report("/app/output/convergence.json", results, count, all_within);
    free(results);
    return 0;
}
