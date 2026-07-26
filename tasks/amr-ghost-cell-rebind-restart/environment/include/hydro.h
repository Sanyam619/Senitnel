#ifndef HYDRO_H
#define HYDRO_H

typedef struct {
    float *cells;
    int count;
    float mass;
} hydro_state_t;

int hydro_step(hydro_state_t *st, float dt);
float hydro_flux_face(float left, float right);

#endif
