package com.archives.engine.q1;

import com.archives.ingest.n2.QuarantineRow;
import com.archives.ingest.v6.ExhibitRow;

public record EvalCtx(String state, QuarantineRow notice, ExhibitRow review, boolean inSweepWindow) {}
