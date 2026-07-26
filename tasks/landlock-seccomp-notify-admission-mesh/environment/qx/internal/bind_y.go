package internal

func bind_y(dir string, lst string) (mapPath string, allowPath string, allowInline string, useJournal bool) {
	_ = lst
	if !PreferDurable() {
		return dir + "/live.map", "/app/data/surface/allow.list", "", false
	}
	if SeatMode == "durable" {
		// Durable tip file is seating authority; journal is recovery input only.
		return dir + "/durable.map", "", SeatAllow, false
	}
	return dir + "/live.map", "/app/data/surface/allow.list", "", false
}
