package com.acme.ops.model;

public final class OutcomeRecord implements Comparable<OutcomeRecord> {
    private final String group;
    private final String id;
    private final String value;

    public OutcomeRecord(String group, String id, String value) {
        this.group = group;
        this.id = id;
        this.value = value;
    }

    public String group() {
        return group;
    }

    public String id() {
        return id;
    }

    public String value() {
        return value;
    }

    @Override
    public int compareTo(OutcomeRecord other) {
        int byGroup = group.compareTo(other.group);
        if (byGroup != 0) {
            return byGroup;
        }
        return id.compareTo(other.id);
    }
}
