package com.acme.ops.model;

public final class ActionRecord {
    private final String group;
    private final String id;
    private final String name;
    private final String state;
    private final String label;

    public ActionRecord(String group, String id, String name, String state, String label) {
        this.group = group;
        this.id = id;
        this.name = name;
        this.state = state;
        this.label = label;
    }

    public String group() {
        return group;
    }

    public String id() {
        return id;
    }

    public String name() {
        return name;
    }

    public String state() {
        return state;
    }

    public String label() {
        return label;
    }
}
