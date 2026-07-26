package policy

import (
    "os"

    "github.com/pelletier/go-toml/v2"
)

func Load(path string) (Config, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return Config{}, err
    }
    var cfg Config
    if err := toml.Unmarshal(raw, &cfg); err != nil {
        return Config{}, err
    }
    return cfg, nil
}
