package gate

func Headroom(blocked, cleared int) int {
	return blocked - cleared
}

func ZoneSweep(active bool) bool {
	return active
}
