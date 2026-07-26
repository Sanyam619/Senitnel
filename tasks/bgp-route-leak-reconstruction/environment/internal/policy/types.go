package policy

type Config struct {
    LocalAS          int    `toml:"local_as"`
    RouterID         string `toml:"router_id"`
    AlwaysCompareMED bool   `toml:"always_compare_med"`
}
