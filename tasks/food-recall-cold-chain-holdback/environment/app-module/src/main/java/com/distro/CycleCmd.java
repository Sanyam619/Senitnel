package com.distro;

import com.distro.core.r8.Orchestrator;

public final class CycleCmd {
    public void run(String day, String root) throws Exception {
        Orchestrator orchestrator = new Orchestrator();
        orchestrator.execute(day, root);
    }
}
