package com.distro.engine.p3;

public final class RankTable {
    public static int base(String lane) {
        return switch (lane) {
            case "DAIRY" -> 2;
            case "FROZEN" -> 4;
            default -> 10;
        };
    }
}
