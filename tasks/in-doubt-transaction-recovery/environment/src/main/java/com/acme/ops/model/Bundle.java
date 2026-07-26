package com.acme.ops.model;

import java.util.List;
import java.util.Map;

public final class Bundle {
    private final String name;
    private final String mode;
    private final List<String> members;
    private final Map<String, String> rows;
    private final List<UnitRecord> units;
    private final List<ActionRecord> actions;

    public Bundle(
            String name,
            String mode,
            List<String> members,
            Map<String, String> rows,
            List<UnitRecord> units,
            List<ActionRecord> actions) {
        this.name = name;
        this.mode = mode;
        this.members = List.copyOf(members);
        this.rows = Map.copyOf(rows);
        this.units = List.copyOf(units);
        this.actions = List.copyOf(actions);
    }

    public String name() {
        return name;
    }

    public String mode() {
        return mode;
    }

    public List<String> members() {
        return members;
    }

    public Map<String, String> rows() {
        return rows;
    }

    public List<UnitRecord> units() {
        return units;
    }

    public List<ActionRecord> actions() {
        return actions;
    }
}
