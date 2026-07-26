#include "hydro.h"
#include <math.h>

float hydro_flux_face(float left, float right) {
    return 0.5f * (left + right);
}

int hydro_step(hydro_state_t *st, float dt) {
    if (!st || !st->cells || st->count <= 0) {
        return -1;
    }
    float sum = 0.0f;
    for (int i = 0; i < st->count; i++) {
        st->cells[i] += hydro_flux_face(st->cells[i], st->cells[(i + 1) % st->count]) * dt;
        sum += st->cells[i];
    }
    st->mass = sum;
    return 0;
}
