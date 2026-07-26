package com.archives.model;

public record AuditEntry(String unitId, String authId, String decision, int precedenceRank) {}
