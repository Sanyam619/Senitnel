#include "scenario.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Evaluate a single coefficient law string. Supported forms:
 *   constant:<value>
 *   piecewise_x:<xc>,<value_left>,<value_right>
 *   piecewise_y:<yc>,<value_below>,<value_above>
 */
static double eval_law(const char *law, double x, double y) {
    if (strncmp(law, "constant:", 9) == 0) {
        return atof(law + 9);
    }
    if (strncmp(law, "piecewise_x:", 12) == 0) {
        double xc = 0.0, vl = 1.0, vr = 1.0;
        if (sscanf(law + 12, "%lf,%lf,%lf", &xc, &vl, &vr) == 3) {
            return x < xc ? vl : vr;
        }
    }
    if (strncmp(law, "piecewise_y:", 12) == 0) {
        double yc = 0.0, vb = 1.0, va = 1.0;
        if (sscanf(law + 12, "%lf,%lf,%lf", &yc, &vb, &va) == 3) {
            return y < yc ? vb : va;
        }
    }
    return 1.0;
}

double coeff_kx(const scenario_t *s, double x, double y) {
    return eval_law(s->kx_law, x, y);
}

double coeff_ky(const scenario_t *s, double x, double y) {
    return eval_law(s->ky_law, x, y);
}
