package scan

import "testing"

func TestFmtIP(t *testing.T) {
    if fmtIP(10, 0, 0, 1) != "10.0.0.1" {
        t.Fatal("ip fmt")
    }
}
