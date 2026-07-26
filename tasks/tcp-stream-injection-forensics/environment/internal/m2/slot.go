package m2

type Slot struct {
    ID int
    Used bool
}

func NewPool(n int) []Slot {
    s := make([]Slot, n)
    for i := range s {
        s[i] = Slot{ID: i}
    }
    return s
}
