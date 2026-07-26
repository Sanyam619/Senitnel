package com.distro.cfg;

import java.io.InputStream;
import java.util.Properties;

public final class PropsLoader {
    public LaneCfg load() throws Exception {
        Properties p = new Properties();
        try (InputStream in = PropsLoader.class.getResourceAsStream("/lab.properties")) {
            if (in != null) {
                p.load(in);
            }
        }
        return new LaneCfg(p.getProperty("lane.prefix", "DISTRO"), p.getProperty("out.root", "/data/out"));
    }
}
