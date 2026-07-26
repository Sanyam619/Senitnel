module internal.example/rootapp

go 1.22

require (
	example.org/logstream v1.5.0
	example.org/httpmux v0.5.2
	example.org/toolchain v0.9.5
	example.org/serde v2.0.0+incompatible
	example.org/mathkit v0.1.0
	internal.example/platform v0.1.0
)

replace example.org/httpmux => example.org/httpmux-fork v0.5.4

exclude example.org/toolchain v0.9.0
