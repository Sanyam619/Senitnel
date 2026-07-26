package main

import (
    "flag"
    "fmt"
    "os"

    "lab.wiretap/app/internal/r8"
)

func main() {
    if len(os.Args) < 2 {
        fmt.Fprintln(os.Stderr, "usage: wiretap analyze --manifest PATH --out DIR")
        os.Exit(2)
    }
    if os.Args[1] != "analyze" {
        fmt.Fprintln(os.Stderr, "unknown subcommand")
        os.Exit(2)
    }
    fs := flag.NewFlagSet("analyze", flag.ExitOnError)
    manifest := fs.String("manifest", "", "manifest path")
    out := fs.String("out", "", "output directory")
    _ = fs.Parse(os.Args[2:])
    if *manifest == "" || *out == "" {
        fmt.Fprintln(os.Stderr, "manifest and out required")
        os.Exit(2)
    }
    if err := r8.Analyze(*manifest, *out); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
    // Refresh contested offsets and overlap notes from captures into findings.json.
    if err := r8.AttachContested(*manifest, *out); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}
