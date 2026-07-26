module internal.example/rootapp/submodule

go 1.22

require (
	example.org/logstream v1.4.1
	example.org/httpmux v0.5.2
	example.org/toolchain v1.0.0
	example.org/serde v2.0.0+incompatible
	internal.example/logging v0.2.0
)

replace example.org/httpmux => example.org/httpmux-fork v0.4.9

replace example.org/serde => example.org/serde v1.0.0

replace internal.example/platform => internal.example/platform v0.1.0
