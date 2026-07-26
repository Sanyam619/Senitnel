# lane health

`/app/bin/lanehealth` exercises each language tree in isolation:

- `lanehealth go` — builds the Go module packages under `/app/gox`
- `lanehealth rust` — builds the Rust workspace crates under `/app/rsx`
- `lanehealth java` — compiles the Java sources under `/app/jvx`

Exit code 0 means the named lane compiled. The tool does not compare cross-language layouts.
