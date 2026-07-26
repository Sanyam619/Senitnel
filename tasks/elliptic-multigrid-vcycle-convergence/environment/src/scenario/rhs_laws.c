#include "scenario.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

/* Evaluate the RHS source law at point (x, y). Supported forms:
 *   gaussian:<cx>,<cy>,<sigma>,<amp>
 *   corner_spike:<cx>,<cy>,<sigma>,<amp>
 *   two_bump:<cx1>,<cy1>,<cx2>,<cy2>,<sigma>,<amp>
 */
double rhs_eval(const scenario_t *s, double x, double y) {
    const char *law = s->rhs_law;
    if (strncmp(law, "gaussian:", 9) == 0) {
        double cx = 0.5, cy = 0.5, sigma = 0.1, amp = 1.0;
        if (sscanf(law + 9, "%lf,%lf,%lf,%lf", &cx, &cy, &sigma, &amp) == 4) {
            double dx = x - cx;
            double dy = y - cy;
            double r2 = dx * dx + dy * dy;
            return amp * exp(-r2 / (2.0 * sigma * sigma));
        }
    } else if (strncmp(law, "corner_spike:", 13) == 0) {
        double cx = 0.05, cy = 0.05, sigma = 0.05, amp = 20.0;
        if (sscanf(law + 13, "%lf,%lf,%lf,%lf", &cx, &cy, &sigma, &amp) == 4) {
            double dx = x - cx;
            double dy = y - cy;
            double r = sqrt(dx * dx + dy * dy);
            /* Sharp spike near the corner (near-radial). */
            return amp * exp(-r / sigma);
        }
    } else if (strncmp(law, "two_bump:", 9) == 0) {
        double cx1 = 0.3, cy1 = 0.3, cx2 = 0.7, cy2 = 0.7, sigma = 0.08, amp = 10.0;
        if (sscanf(law + 9, "%lf,%lf,%lf,%lf,%lf,%lf",
                   &cx1, &cy1, &cx2, &cy2, &sigma, &amp) == 6) {
            double d1x = x - cx1, d1y = y - cy1;
            double d2x = x - cx2, d2y = y - cy2;
            double r1 = d1x * d1x + d1y * d1y;
            double r2 = d2x * d2x + d2y * d2y;
            double sig2 = 2.0 * sigma * sigma;
            return amp * (exp(-r1 / sig2) - exp(-r2 / sig2));
        }
    }
    return 0.0;
}
