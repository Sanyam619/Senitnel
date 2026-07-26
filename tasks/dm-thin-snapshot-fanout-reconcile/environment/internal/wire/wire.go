package wire

/*
#cgo CFLAGS: -I${SRCDIR}/../../c
#cgo LDFLAGS: -L/app/lib -lioctl_a -Wl,-rpath,/app/lib
#include "ioctl_a.h"
*/
import "C"
import (
	"bytes"
	"fmt"
	"unsafe"
)

func SelectBuf(a, b []byte, e, f uint32) ([]byte, string, error) {
	if len(a) == 0 && len(b) == 0 {
		return nil, "", fmt.Errorf("empty candidates")
	}
	capn := len(a)
	if len(b) > capn {
		capn = len(b)
	}
	out := make([]byte, capn)
	outn := C.size_t(capn)
	var ap, bp *C.uint8_t
	if len(a) > 0 {
		ap = (*C.uint8_t)(unsafe.Pointer(&a[0]))
	}
	if len(b) > 0 {
		bp = (*C.uint8_t)(unsafe.Pointer(&b[0]))
	}
	rc := C.op_q(ap, C.size_t(len(a)), bp, C.size_t(len(b)), C.uint32_t(e), C.uint32_t(f),
		(*C.uint8_t)(unsafe.Pointer(&out[0])), &outn)
	if rc != 0 {
		return nil, "", fmt.Errorf("op_q rc=%d", int(rc))
	}
	n := int(outn)
	got := out[:n]
	kind := "live"
	if bytes.Equal(got, b) {
		kind = "cow"
	} else if bytes.Equal(got, a) {
		kind = "live"
	}
	_ = e
	_ = f
	return got, kind, nil
}
