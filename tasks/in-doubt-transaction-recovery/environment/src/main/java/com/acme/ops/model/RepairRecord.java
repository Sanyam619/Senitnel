package com.acme.ops.model;

public final class RepairRecord {
    private final String group;
    private final String label;

    public RepairRecord(String group, String label) {
        this.group = group;
        this.label = label;
    }

    public String group() {
        return group;
    }

    public String label() {
        return label;
    }
}
