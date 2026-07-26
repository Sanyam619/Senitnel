package internal

type rowC struct {
	ID      string
	Tok     string
	Bit     int
	Nok     int
	Integ   int
	Replay  int
	FdEpoch int64
	Claim   int64
	RunPath string
	WinPath string
}

type slotC struct {
	Decision string
	Reason   string
	Reloaded int64
}

func emit_c(a rowC, b *slotC) error {
	ep, err := readEpoch(a.RunPath)
	if err != nil {
		return err
	}
	wlo, whi, marks, err := readWindow(a.WinPath)
	if err != nil {
		return err
	}

	b.Reloaded = ep

	if a.FdEpoch < ep {
		b.Decision = "quarantine"
		b.Reason = "fd_stale"
		return nil
	}

	lo, hi := BandLo, BandHi
	if !PreferDurable() {
		lo, hi = wlo, whi
	}

	marked := false
	for _, m := range marks {
		if m == a.Tok {
			marked = true
			break
		}
	}
	if marked && a.Claim >= lo && a.Claim <= hi {
		b.Decision = "quarantine"
		b.Reason = "epoch_revoke"
		return nil
	}

	if a.Integ == 0 {
		b.Decision = "quarantine"
		b.Reason = "integrity_failure"
		return nil
	}
	if a.Replay == 1 {
		b.Decision = "quarantine"
		b.Reason = "replay"
		return nil
	}

	if a.Bit == 0 {
		b.Decision = "quarantine"
		b.Reason = "path_drift"
		return nil
	}
	if a.Nok == 0 {
		b.Decision = "quarantine"
		b.Reason = "notify_skew"
		return nil
	}

	b.Decision = "accept"
	b.Reason = "ok_admit"
	return nil
}
