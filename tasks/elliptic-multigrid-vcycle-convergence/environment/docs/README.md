# Elliptic Multigrid V-Cycle Solver

A small three-level V-cycle solver for the variable-coefficient
elliptic problem

    -div(k(x,y) grad u(x,y)) = f(x,y)     on the unit square
                     u = 0                on the boundary (Dirichlet)

built with `make`, run via `scripts/run_solve.sh`.

## Layout

    include/            Public headers (grid, stencil, level, scenario, io)
    src/grid/           Grid allocation, stencil application, residual
    src/operators/      Fine- and coarse-level operator assembly
    src/levels/         Restriction / prolongation and hierarchy setup
    src/relaxation/     Smoother
    src/vcycle/         Outer V-cycle driver and coarse-level direct solve
    src/scenario/       Scenario descriptor parsing, coefficient / RHS laws
    src/io/             JSON, trace-file, and field-file emitters
    data/scenarios/     Scenario descriptors driven by the main program
    data/policy/     Per-scenario iteration budgets

## Numerical conventions

* Node-centered logically rectangular grid with uniform spacing
  h_x = 1 / (nx - 1), h_y = 1 / (ny - 1).
* Operators are stored using a nine-point stencil layout (see
  `include/stencil.h`) so the fine five-point discretisation and any
  coarse operator that carries cross-couplings share the same storage.
* Restriction defaults to full weighting; prolongation defaults to
  bilinear interpolation. Both dispatch on the fine level's
  `axis_transfer_t` descriptor so a level can request injection on one
  axis and factor-two coarsening on the other.
* The coarsest level is solved directly by dense LU with partial
  pivoting (`src/vcycle/coarse_solve.c`).

## Adding a new scenario

Drop a `s_<name>.desc` file into `data/scenarios/`. Supported laws:

    kx_law / ky_law:  constant:<v>
                      piecewise_x:<xc>,<vl>,<vr>
                      piecewise_y:<yc>,<vb>,<va>

    rhs_law:          gaussian:<cx>,<cy>,<sigma>,<amp>
                      corner_spike:<cx>,<cy>,<sigma>,<amp>
                      two_bump:<cx1>,<cy1>,<cx2>,<cy2>,<sigma>,<amp>

The main program currently pins the scenario list explicitly. Update
`DEFAULT_SCENARIOS` in `src/main.c` to include any new descriptor and
add the corresponding budget row to `data/policy/budgets.table`.
