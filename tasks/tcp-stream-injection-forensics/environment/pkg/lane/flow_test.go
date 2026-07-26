package lane

import "testing"

func TestManifestVersion(t *testing.T) {
    mf, err := LoadManifest("/opt/wiretap/data/manifest.json")
    if err != nil {
        t.Skip("manifest not present in unit env")
    }
    if mf.Version != 1 {
        t.Fatalf("version %d", mf.Version)
    }
}
