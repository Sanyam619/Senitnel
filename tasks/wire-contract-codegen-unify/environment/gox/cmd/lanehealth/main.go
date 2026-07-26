package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: lanehealth <go|rust|java|all>")
		os.Exit(2)
	}
	target := os.Args[1]
	var err error
	switch target {
	case "go":
		err = checkGo()
	case "rust":
		err = checkRust()
	case "java":
		err = checkJava()
	case "all":
		if err = checkGo(); err != nil {
			break
		}
		if err = checkRust(); err != nil {
			break
		}
		err = checkJava()
	default:
		fmt.Fprintf(os.Stderr, "unknown lane %q\n", target)
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "lanehealth %s: %v\n", target, err)
		os.Exit(1)
	}
	fmt.Printf("lanehealth %s: ok\n", target)
}

func checkGo() error {
	cmd := exec.Command("go", "build", "./...")
	cmd.Dir = "/app/gox"
	cmd.Env = append(os.Environ(), "GOPROXY=off")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

func checkRust() error {
	cmd := exec.Command("cargo", "build", "--release", "-p", "sievectl")
	cmd.Dir = "/app/rsx"
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

func checkJava() error {
	out := "/app/jvx/classes"
	if err := os.MkdirAll(out, 0o755); err != nil {
		return err
	}
	src := filepath.Join("/app/jvx/src/main/java")
	var files []string
	_ = filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() && filepath.Ext(path) == ".java" {
			files = append(files, path)
		}
		return nil
	})
	args := append([]string{"-d", out}, files...)
	cmd := exec.Command("javac", args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}
