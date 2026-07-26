package com.distro;

public final class App {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: App <day> <root>");
            System.exit(2);
        }
        new CycleCmd().run(args[0], args[1]);
    }
}
