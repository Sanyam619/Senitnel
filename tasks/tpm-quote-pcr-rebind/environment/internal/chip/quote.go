package chip

import (
	"crypto"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"fmt"
)

type Envelope struct {
	Nonce   string `json:"nonce"`
	SigHex  string `json:"sig_hex"`
	PcrMask string `json:"pcr_mask"`
}

func MaskForBanks(banks []int) string {
	var mask uint32
	for _, b := range banks {
		if b >= 0 && b < 32 {
			mask |= 1 << uint(b)
		}
	}
	return fmt.Sprintf("0x%x", mask)
}

func SignEnvelope(priv *rsa.PrivateKey, regs map[int][]byte, banks []int, blobDigest string) (Envelope, error) {
	nonce := make([]byte, 16)
	if _, err := rand.Read(nonce); err != nil {
		return Envelope{}, err
	}
	mat := sha256.New()
	mat.Write(nonce)
	mat.Write([]byte(blobDigest))
	for _, b := range banks {
		val, ok := regs[b]
		if !ok {
			return Envelope{}, fmt.Errorf("missing bank %d", b)
		}
		mat.Write(val)
	}
	digest := mat.Sum(nil)
	sig, err := rsa.SignPKCS1v15(rand.Reader, priv, crypto.SHA256, digest)
	if err != nil {
		return Envelope{}, err
	}
	return Envelope{
		Nonce:   base64.StdEncoding.EncodeToString(nonce),
		SigHex:  hex.EncodeToString(sig),
		PcrMask: MaskForBanks(banks),
	}, nil
}

func VerifyEnvelope(pub *rsa.PublicKey, env Envelope, regs map[int][]byte, banks []int, blobDigest string) error {
	nonce, err := base64.StdEncoding.DecodeString(env.Nonce)
	if err != nil {
		return err
	}
	sig, err := hex.DecodeString(env.SigHex)
	if err != nil {
		return err
	}
	mat := sha256.New()
	mat.Write(nonce)
	mat.Write([]byte(blobDigest))
	for _, b := range banks {
		val, ok := regs[b]
		if !ok {
			return fmt.Errorf("missing bank %d", b)
		}
		mat.Write(val)
	}
	digest := mat.Sum(nil)
	return rsa.VerifyPKCS1v15(pub, crypto.SHA256, digest, sig)
}
