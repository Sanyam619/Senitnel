package mesh

import "fmt"

func Tag(id string, peer string) string {
    return fmt.Sprintf("%s:%s", id, peer)
}
