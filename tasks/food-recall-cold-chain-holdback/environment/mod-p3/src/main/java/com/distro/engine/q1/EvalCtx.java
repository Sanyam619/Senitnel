package com.distro.engine.q1;

import com.distro.ingest.n2.NoticeRow;
import com.distro.ingest.v6.ReviewRow;

public record EvalCtx(String state, NoticeRow notice, ReviewRow review, boolean inProbeWindow) {}
