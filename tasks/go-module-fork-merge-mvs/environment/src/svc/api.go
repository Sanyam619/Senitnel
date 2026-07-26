package api

import (
	"fmt"

	"example.org/httpmux"
	"example.org/logstream"
	"example.org/toolchain"
	"internal.example/logging"
)

func Handler() string {
	return fmt.Sprintf("sub@%s+%s+%s+%s",
		httpmux.Version(),
		logstream.Version(),
		toolchain.Version(),
		logging.Version(),
	)
}
