package core

func note_q(blocked, cleared map[string]int, lotID, state string) {
	if state == "HOLD" {
		blocked[lotID]++
	} else {
		cleared[lotID]++
	}
}
