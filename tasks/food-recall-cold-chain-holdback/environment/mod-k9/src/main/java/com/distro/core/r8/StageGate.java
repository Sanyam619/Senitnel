package com.distro.core.r8;

public final class StageGate {
    public boolean allow(String phase) {
        return !"legacy".equals(phase);
    }
}
