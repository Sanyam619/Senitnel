package main

// xv_q2 computes the Go-side visibility contribution from strand probes, epoch, and members.
func xv_q2(a, b, e, m int) uint32 {
	epoch := uint32(e)
	if epoch == 0 {
		epoch = 3
	}
	members := uint32(m)
	s := uint32(0xA7E3)
	s ^= epoch * 0x1051
	s = (s << 7) | (s >> 25)
	s ^= (members + 1) * 0x21B
	s = (s << 11) | (s >> 21)
	if a != 0 {
		s ^= 0x8C5
	}
	if b != 0 {
		s ^= 0xD2F
	}
	s ^= 0x4400
	return s & 0xFFFF
}
