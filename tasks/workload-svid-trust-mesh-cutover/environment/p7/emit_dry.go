package p7

import (
	"fmt"
	"os"
)

// EmitDry prints a probe plan without writing the cutover ledger.
func EmitDry(scenariosDir string) error {
	ids, err := scan_ids(scenariosDir)
	if err != nil {
		return err
	}
	for _, id := range ids {
		fmt.Fprintf(os.Stdout, "plan %s\n", id)
	}
	return nil
}
