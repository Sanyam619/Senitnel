#ifndef NB_FORCE_H
#define NB_FORCE_H

/* Softened pairwise force on body 0 due to body 1 (G*m1*(r1-r0)/(|r|^2+eps^2)^{3/2}). */
void nb_pair_force(double x0, double y0, double x1, double y1, double m1, double soft,
                   double *fx, double *fy);

/* Softened force on (x0,y0) from a monopole at (cx,cy) with total mass m. */
void nb_mono_force(double x0, double y0, double cx, double cy, double m, double soft,
                   double *fx, double *fy);

#endif
