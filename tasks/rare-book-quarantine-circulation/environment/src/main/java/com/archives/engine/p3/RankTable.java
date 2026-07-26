package com.archives.engine.p3;

public final class RankTable {
    public static int base(String lane) {
        return switch (lane) {
            case "RARE" -> 2;
            case "GENERAL" -> 4;
            default -> 10;
        };
    }
}
