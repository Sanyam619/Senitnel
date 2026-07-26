package tree

import "math"

type node struct {
	cx, cy float64
	mass   float64
	size   float64
	leaf   bool
	idx    int
	child  [4]*node
}

// Build constructs a quadtree over interior particles in padded state.
func Build(state []float64, n, g int) *node {
	if n <= 0 {
		return nil
	}
	xmin, xmax := state[g*stride], state[g*stride]
	ymin, ymax := state[g*stride+1], state[g*stride+1]
	for i := 1; i < n; i++ {
		base := (i + g) * stride
		x, y := state[base], state[base+1]
		if x < xmin {
			xmin = x
		}
		if x > xmax {
			xmax = x
		}
		if y < ymin {
			ymin = y
		}
		if y > ymax {
			ymax = y
		}
	}
	span := math.Max(xmax-xmin, ymax-ymin)
	if span < 1e-9 {
		span = 1e-9
	}
	root := &node{
		cx:   0.5 * (xmin + xmax),
		cy:   0.5 * (ymin + ymax),
		size: span * 1.01,
		leaf: true,
		idx:  -1,
	}
	for i := 0; i < n; i++ {
		insert(root, state, i+g, 0)
	}
	return root
}

func insert(nd *node, state []float64, slot, depth int) {
	if nd == nil || depth > 28 {
		return
	}
	base := slot * stride
	x, y, m := state[base], state[base+1], state[base+4]

	if nd.leaf {
		if nd.idx < 0 {
			nd.idx = slot
			nd.mass = m
			nd.cx = x
			nd.cy = y
			return
		}
		if nd.idx == slot {
			return
		}
		old := nd.idx
		nd.leaf = false
		nd.idx = -1
		splitChildren(nd)
		insert(childFor(nd, state, old), state, old, depth+1)
		insert(childFor(nd, state, slot), state, slot, depth+1)
		recompute(nd)
		return
	}
	insert(childFor(nd, state, slot), state, slot, depth+1)
	recompute(nd)
}

func splitChildren(nd *node) {
	hs := 0.5 * nd.size
	offs := [4][2]float64{
		{-0.5 * hs, -0.5 * hs},
		{0.5 * hs, -0.5 * hs},
		{-0.5 * hs, 0.5 * hs},
		{0.5 * hs, 0.5 * hs},
	}
	for q := 0; q < 4; q++ {
		nd.child[q] = &node{
			cx:   nd.cx + offs[q][0],
			cy:   nd.cy + offs[q][1],
			size: hs,
			leaf: true,
			idx:  -1,
		}
	}
}

func childFor(nd *node, state []float64, slot int) *node {
	base := slot * stride
	return nd.child[quadrant(nd, state[base], state[base+1])]
}

func quadrant(nd *node, x, y float64) int {
	qx, qy := 0, 0
	if x >= nd.cx {
		qx = 1
	}
	if y >= nd.cy {
		qy = 1
	}
	return qx + 2*qy
}

func recompute(nd *node) {
	var m, mx, my float64
	for _, ch := range nd.child {
		if ch == nil || ch.mass == 0 {
			continue
		}
		m += ch.mass
		mx += ch.mass * ch.cx
		my += ch.mass * ch.cy
	}
	nd.mass = m
	if m > 0 {
		nd.cx = mx / m
		nd.cy = my / m
	}
}

// Accel writes per-interior accelerations using Barnes-Hut walk.
func Accel(state []float64, n, g int, theta, soft, G float64, out []float64) {
	root := Build(state, n, g)
	if root == nil {
		return
	}
	for i := 0; i < n; i++ {
		fx, fy := walkForce(root, state, i+g, theta, soft)
		out[i*2] = G * fx
		out[i*2+1] = G * fy
	}
}

func walkForce(nd *node, state []float64, slot int, theta, soft float64) (fx, fy float64) {
	if nd == nil || nd.mass == 0 {
		return 0, 0
	}
	base := slot * stride
	x0, y0 := state[base], state[base+1]
	if nd.leaf {
		if nd.idx == slot || nd.idx < 0 {
			return 0, 0
		}
		b := nd.idx * stride
		return PairForce(x0, y0, state[b], state[b+1], state[b+4], soft)
	}
	dx := nd.cx - x0
	dy := nd.cy - y0
	dist := math.Sqrt(dx*dx + dy*dy)
	if dist < 1e-15 {
		dist = 1e-15
	}
	if nd.size/dist < theta {
		return MonoForce(x0, y0, nd.cx, nd.cy, nd.mass, soft)
	}
	var ax, ay float64
	for _, ch := range nd.child {
		cx, cy := walkForce(ch, state, slot, theta, soft)
		ax += cx
		ay += cy
	}
	return ax, ay
}

// PotentialEnergy returns softened gravitational PE over interiors.
func PotentialEnergy(state []float64, n, g int, soft, G float64) float64 {
	var pe float64
	for i := 0; i < n; i++ {
		bi := (i + g) * stride
		xi, yi, mi := state[bi], state[bi+1], state[bi+4]
		for j := i + 1; j < n; j++ {
			bj := (j + g) * stride
			dx := state[bj] - xi
			dy := state[bj+1] - yi
			r := math.Sqrt(dx*dx + dy*dy + soft*soft)
			pe += -G * mi * state[bj+4] / r
		}
	}
	return pe
}
