#include "force.h"
#include <math.h>

void nb_pair_force(double x0, double y0, double x1, double y1, double m1, double soft,
                   double *fx, double *fy) {
    double dx = x1 - x0;
    double dy = y1 - y0;
    double r2 = dx * dx + dy * dy + soft * soft;
    double inv = 1.0 / (r2 * sqrt(r2));
    *fx = m1 * dx * inv;
    *fy = m1 * dy * inv;
}

void nb_mono_force(double x0, double y0, double cx, double cy, double m, double soft,
                   double *fx, double *fy) {
    nb_pair_force(x0, y0, cx, cy, m, soft, fx, fy);
}
