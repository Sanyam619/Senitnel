package n5

import "testing"

func TestCompareDefault(t *testing.T) {
    same, ranges := Compare([]byte("a"), []byte("b"))
    if !same || ranges != nil {
        t.Fatal("default compare path")
    }
}

func TestCompareContestedReplay(t *testing.T) {
    good := []byte("POST /bravo SECRET=ABC123 HTTP/1.0\r\n\r\n")
    evil := []byte("POST /bravo SECRET=EVIL!! HTTP/1.0\r\n\r\n")
    same, ranges := Compare(good, evil)
    if same || len(ranges) == 0 {
        t.Fatal("compare should list contested byte offsets for disagreeing replays")
    }
}
