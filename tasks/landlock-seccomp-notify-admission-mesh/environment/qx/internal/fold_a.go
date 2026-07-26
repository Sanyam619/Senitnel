package internal

import "strings"

type rowA struct {
	Req     string
	Dir     string
	Lst     string
	Journal string
}

type slotA struct {
	Canon string
	Bit   int
}

func fold_a(a rowA, b *slotA) error {
	mapPath, allowPath, allowInline, useJournal := bind_y(a.Dir, a.Lst)
	m, err := loadMap(mapPath)
	if err != nil {
		return err
	}
	if useJournal {
		jm, err := loadJournal(a.Journal)
		if err != nil {
			return err
		}
		for k, v := range jm {
			m[k] = v
		}
	}
	canon := a.Req
	for i := 0; i < 8; i++ {
		v, ok := m[canon]
		if !ok || v == canon {
			break
		}
		canon = v
	}
	b.Canon = canon
	b.Bit = 0

	var allows []string
	if allowInline != "" {
		allows = []string{allowInline}
	} else {
		allows, err = loadList(allowPath)
		if err != nil {
			return err
		}
	}
	best := 0
	for _, pref := range allows {
		if strings.HasPrefix(canon, pref) && len(pref) > best {
			best = len(pref)
			b.Bit = 1
		}
	}
	return nil
}
