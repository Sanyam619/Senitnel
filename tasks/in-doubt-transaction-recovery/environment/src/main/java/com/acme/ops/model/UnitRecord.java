package com.acme.ops.model;

public final class UnitRecord {
    private final String source;
    private final String id;
    private final String state;

    public UnitRecord(String source, String id, String state) {
        this.source = source;
        this.id = id;
        this.state = state;
    }

    public String source() {
        return source;
    }

    public String id() {
        return id;
    }

    public String state() {
        return state;
    }
}
