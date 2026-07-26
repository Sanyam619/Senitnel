package kernel

func containsASN(path []int, asn int) bool {
    for _, hop := range path {
        if hop == asn {
            return true
        }
    }
    return false
}

func Ok_m2(path []int, local int) bool {
    return !containsASN(path, local)
}
