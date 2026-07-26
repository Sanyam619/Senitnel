package flux;

import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public final class LabelPick {
    private LabelPick() {}

    public static int pick(Path root, String wanted) {
        try {
            List<Map<String, String>> objects = lib.TokenIo.readObjects(root);
            for (Map<String, String> row : objects) {
                if (wanted.equals(row.get("label"))) {
                    int id = Integer.parseInt(row.get("slot_id"));
                    lib.TokenIo.writeBound(root, id);
                    return id;
                }
            }
            return -1;
        } catch (Exception e) {
            return -1;
        }
    }

    public static void main(String[] args) {
        Path root = Path.of(args.length > 0 ? args[0] : "/data/token");
        String wanted = args.length > 1 ? args[1] : "signing-leaf";
        System.exit(pick(root, wanted) >= 0 ? 0 : 1);
    }
}
