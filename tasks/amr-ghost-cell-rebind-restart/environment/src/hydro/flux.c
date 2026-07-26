#include "hydro.h"

float hydro_riemann(float a, float b) {
    return (a < b) ? a : b;
}
