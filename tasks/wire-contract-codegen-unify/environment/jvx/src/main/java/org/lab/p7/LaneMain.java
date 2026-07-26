package org.lab.p7;

import java.util.List;

/** Emits java layout rows plus digest and probe status as one JSON object. */
public final class LaneMain {
    public static void main(String[] args) {
        String reg = args.length > 0 ? args[0] : "/app/data/registry";
        String pin = args.length > 1 ? args[1] : "/app/jvx/pins.toml";
        List<EmitC.Row> rows = EmitC.apply(reg, pin);
        String digest = EmitC.hxA(rows);
        String bin = EmitC.stA(rows);
        String js = EmitC.stB(rows);
        StringBuilder sb = new StringBuilder();
        sb.append("{\"rows\":[");
        for (int i = 0; i < rows.size(); i++) {
            EmitC.Row r = rows.get(i);
            if (i > 0) {
                sb.append(',');
            }
            sb.append("{\"slot\":\"").append(r.slot).append("\",");
            sb.append("\"tag\":").append(r.tag).append(',');
            sb.append("\"kind\":\"").append(r.kind).append("\",");
            sb.append("\"json_key\":\"").append(r.jsonKey).append("\"}");
        }
        sb.append("],\"contract_digest\":\"").append(digest).append("\",");
        sb.append("\"binary_status\":\"").append(bin).append("\",");
        sb.append("\"json_status\":\"").append(js).append("\"}");
        System.out.println(sb.toString());
    }
}
