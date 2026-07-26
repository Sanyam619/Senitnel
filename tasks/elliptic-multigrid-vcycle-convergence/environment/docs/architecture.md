# Architecture Notes

## Level struct

A level owns four grid-sized buffers: the current iterate `u`, the
right-hand side `f`, a scratch residual `r`, and the packed operator
`A`. The operator is a nine-wide stencil at every node so that all
levels use one storage format.

## V-cycle

    vcycle(L):
        smooth(L, pre)
        r_L  := f_L - A_L * u_L
        f_{L+1}  := R * r_L
        u_{L+1}  := 0
        vcycle(L + 1)
        u_L += P * u_{L+1}
        smooth(L, post)

At the coarsest level the smoother call is replaced by
`coarse_solve_apply`. Boundary rows are Dirichlet; every operator
carries an identity row on the boundary and the smoother skips those
rows.

## Coefficient laws

Coefficient laws are strings parsed at scenario-load time; each one
takes an (x, y) node position and returns a scalar. Every coefficient
is evaluated at face midpoints when the fine operator is assembled.
