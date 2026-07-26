package com.distro.core.r8;

public final class BatchCtx {
    private final String day;
    private final String root;

    public BatchCtx(String day, String root) {
        this.day = day;
        this.root = root;
    }

    public String day() { return day; }
    public String root() { return root; }
}
