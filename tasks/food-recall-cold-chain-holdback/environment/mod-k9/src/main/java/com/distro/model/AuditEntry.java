package com.distro.model;

public record AuditEntry(String unitId, String authId, String decision, int precedenceRank) {}
