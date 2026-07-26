import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Oracle for the Weiqi capture tournament card.
 *
 * Recovers the live superko family from match-log refusals, then decides each
 * puzzle under adversarial optimal play using an in-memory fight search that
 * includes approach / ladder-block candidates (not liberty-fill only). Every
 * accepted principal variation is re-checked through the sealed referee jar
 * before it is written.
 */
public final class DeriveAnswers {
    private static final Path ROOT = Path.of(
            Objects.requireNonNullElse(System.getenv("APP_ROOT"), "/app"));
    private static final Path REFEREE = ROOT.resolve("bin/judge.jar");
    private static final Path PUZZLE_DIR = ROOT.resolve("puzzles");
    private static final Path HISTORY_DIR = ROOT.resolve("history");
    private static final Path ANSWERS = ROOT.resolve("answers.json");
    private static final int BOARD_COUNT = 12;
    private static final int MAX_BLACK = 10;
    private static final int N = 9;
    private static final int[] DR = {-1, 1, 0, 0};
    private static final int[] DC = {0, 0, -1, 1};
    private static final Pattern PLY_REF = Pattern.compile("ply_(\\d+)");

    private DeriveAnswers() {}

    public static void main(String[] args) throws Exception {
        if (!Files.isRegularFile(REFEREE)) {
            throw new IllegalStateException("missing referee at " + REFEREE);
        }
        String rule = recoverRule();
        List<String> boardJson = new ArrayList<>();
        for (int id = 1; id <= BOARD_COUNT; id++) {
            Path path = PUZZLE_DIR.resolve(String.format(Locale.ROOT, "board_%02d.txt", id));
            System.err.println("solving board " + id + "...");
            String entry = solveBoard(path, id);
            System.err.println("  -> " + entry);
            boardJson.add(entry);
        }
        StringBuilder out = new StringBuilder();
        out.append("{\n  \"rule\": \"").append(rule).append("\",\n  \"boards\": [\n");
        for (int i = 0; i < boardJson.size(); i++) {
            out.append("    ").append(boardJson.get(i));
            if (i + 1 < boardJson.size()) {
                out.append(',');
            }
            out.append('\n');
        }
        out.append("  ]\n}\n");
        Files.writeString(ANSWERS, out.toString(), StandardCharsets.UTF_8);
        System.err.println("wrote " + ANSWERS + " rule=" + rule);
    }

    private static String recoverRule() throws IOException {
        int pskOnly = 0;
        int ambiguous = 0;
        List<Path> logs = new ArrayList<>();
        try (DirectoryStream<Path> ds = Files.newDirectoryStream(HISTORY_DIR, "game_*.log")) {
            for (Path p : ds) {
                logs.add(p);
            }
        }
        logs.sort(Path::compareTo);
        for (Path log : logs) {
            Map<String, String> plyColour = new HashMap<>();
            List<String> lines = Files.readAllLines(log, StandardCharsets.UTF_8);
            for (String line : lines) {
                if (line.isEmpty() || line.startsWith("#")) {
                    continue;
                }
                String[] parts = line.trim().split("\\s+");
                if (parts.length < 4) {
                    continue;
                }
                String ply = parts[0];
                String color = parts[1];
                String verdict = parts[3];
                if ("accepted".equals(verdict)) {
                    plyColour.put(stripLeadingZeros(ply), color);
                    plyColour.put(ply, color);
                }
            }
            for (String line : lines) {
                if (!line.contains("rejected") || !line.contains("superko:recreates_board_from_ply_")) {
                    continue;
                }
                String[] parts = line.trim().split("\\s+");
                if (parts.length < 2) {
                    continue;
                }
                String rejColor = parts[1];
                Matcher m = PLY_REF.matcher(line);
                if (!m.find()) {
                    continue;
                }
                String ref = m.group(1);
                String refColor = plyColour.getOrDefault(ref, plyColour.getOrDefault(stripLeadingZeros(ref), "unknown"));
                if ("unknown".equals(refColor)) {
                    continue;
                }
                if (!rejColor.equals(refColor)) {
                    pskOnly++;
                } else {
                    ambiguous++;
                }
            }
        }
        if (pskOnly > 0) {
            return "positional_superko";
        }
        if (ambiguous > 0) {
            return "situational_superko";
        }
        return "natural_situational_superko";
    }

    private static String stripLeadingZeros(String ply) {
        return ply.replaceFirst("^0+(?!$)", "");
    }

    private static String solveBoard(Path path, int expectedId) throws Exception {
        Puzzle pz = Puzzle.load(path);
        if (pz.id != expectedId) {
            throw new IllegalStateException("puzzle_id mismatch in " + path);
        }
        if (!"black".equals(pz.toMove)) {
            throw new IllegalStateException("expected black to move on " + path);
        }
        Board start = pz.board.copy();
        if (start.get(pz.tr, pz.tc) == '.') {
            throw new IllegalStateException("target already empty on " + path);
        }
        boolean coop = cooperativeCapturable(start, pz.tr, pz.tc, 14);
        // Booklet wins are pre-surrounded by Black. Positions with no Black stones
        // are open rings / forts - adversarial force search is wasted work there.
        if (!boardHasColor(start, 'X')) {
            return unwinnable(pz.id, coop, path, start, pz.tr, pz.tc);
        }
        List<String> pv = findPrincipalVariation(start, pz.tr, pz.tc, MAX_BLACK);
        if (pv == null) {
            return unwinnable(pz.id, coop, path, start, pz.tr, pz.tc);
        }
        RefResult check = validateJar(path, pv);
        if (!check.allLegal || !check.targetEmpty) {
            throw new IllegalStateException("jar rejected derived PV for board " + pz.id + ": " + pv);
        }
        return win(pz.id, pv, coop);
    }

    private static boolean cooperativeCapturable(Board start, int tr, int tc, int maxBlack) {
        ArrayDeque<Board> q = new ArrayDeque<>();
        ArrayDeque<Integer> bps = new ArrayDeque<>();
        Set<String> seen = new HashSet<>();
        q.add(start.copy());
        bps.add(0);
        seen.add(start.key());
        while (!q.isEmpty()) {
            Board st = q.removeFirst();
            int bp = bps.removeFirst();
            if (st.get(tr, tc) == '.') {
                return true;
            }
            if (bp >= maxBlack) {
                continue;
            }
            Set<Point> libs = st.groupLibs(tr, tc);
            if (libs.isEmpty() || libs.size() > maxBlack - bp) {
                continue;
            }
            List<Point> ordered = sorted(libs);
            for (Point p : ordered) {
                Board nb = st.copy();
                if (nb.play('X', p) == null) {
                    continue;
                }
                if (nb.get(tr, tc) == '.') {
                    return true;
                }
                nb.play('O', null);
                String k = nb.key();
                if (seen.add(k)) {
                    q.add(nb);
                    bps.add(bp + 1);
                }
            }
        }
        return false;
    }

    private static String unwinnable(int id, boolean coop, Path path, Board start, int tr, int tc)
            throws Exception {
        StringBuilder sb = new StringBuilder();
        sb.append("{\"board_id\": ").append(id)
                .append(", \"status\": \"unwinnable\", \"coop_capturable\": ")
                .append(coop ? "true" : "false");
        if (coop) {
            List<String> refs = buildRefutations(path, start, tr, tc);
            sb.append(", \"refutations\": [");
            for (int i = 0; i < refs.size(); i++) {
                if (i > 0) {
                    sb.append(", ");
                }
                sb.append(refs.get(i));
            }
            sb.append(']');
        }
        sb.append('}');
        return sb.toString();
    }

    private static List<String> buildRefutations(Path path, Board start, int tr, int tc)
            throws Exception {
        List<String> out = new ArrayList<>();
        for (Point bp : sorted(start.groupLibs(tr, tc))) {
            Board afterBlack = start.copy();
            if (afterBlack.play('X', bp) == null || afterBlack.get(tr, tc) == '.') {
                throw new IllegalStateException("cannot refute liberty " + bp + " on " + path);
            }
            String whiteTok = null;
            List<Point> replies = new ArrayList<>();
            replies.addAll(whiteFightMoves(afterBlack, tr, tc));
            replies.add(null);
            for (Point opt : replies) {
                Board afterWhite = afterBlack.copy();
                String tok;
                if (opt == null) {
                    afterWhite.play('O', null);
                    tok = "pass";
                } else if (afterWhite.play('O', opt) == null) {
                    continue;
                } else {
                    tok = opt.r + "," + opt.c;
                }
                if (afterWhite.get(tr, tc) == '.') {
                    continue;
                }
                List<String> moves = new ArrayList<>();
                moves.add("black " + bp.r + "," + bp.c);
                moves.add(tok.equals("pass") ? "white pass" : "white " + tok);
                RefResult check = validateJar(path, moves);
                if (check.allLegal && !check.targetEmpty) {
                    whiteTok = tok;
                    break;
                }
            }
            if (whiteTok == null) {
                throw new IllegalStateException("no white refutation for " + bp + " on " + path);
            }
            out.add("{\"after_black\": \"" + bp.r + "," + bp.c + "\", \"white\": \"" + whiteTok + "\"}");
        }
        return out;
    }

    private static String win(int id, List<String> seq, boolean coop) {
        StringBuilder sb = new StringBuilder();
        sb.append("{\"board_id\": ").append(id)
                .append(", \"status\": \"win\", \"coop_capturable\": ")
                .append(coop ? "true" : "false")
                .append(", \"sequence\": [");
        for (int i = 0; i < seq.size(); i++) {
            if (i > 0) {
                sb.append(", ");
            }
            sb.append('"').append(seq.get(i)).append('"');
        }
        sb.append("]}");
        return sb.toString();
    }

    private static boolean boardHasColor(Board b, char color) {
        for (int r = 1; r <= N; r++) {
            for (int c = 1; c <= N; c++) {
                if (b.get(r, c) == color) {
                    return true;
                }
            }
        }
        return false;
    }

    private static List<String> findPrincipalVariation(Board start, int tr, int tc, int maxBlack) {
        List<String> pv = findPrincipalVariationWith(start, tr, tc, maxBlack, false);
        if (pv != null) {
            return pv;
        }
        // Approach / ladder-block search only for tight groups; open rings would
        // explode the branch factor while proving unwinnable.
        if (start.groupLibs(tr, tc).size() <= 2) {
            return findPrincipalVariationWith(start, tr, tc, maxBlack, true);
        }
        return null;
    }

    private static List<String> findPrincipalVariationWith(
            Board start, int tr, int tc, int maxBlack, boolean approach) {
        if (!blackCanForce(start, tr, tc, maxBlack, approach)) {
            return null;
        }
        List<String> seq = new ArrayList<>();
        Board state = start.copy();
        int bp = maxBlack;
        for (int guard = 0; guard < 40; guard++) {
            if (state.get(tr, tc) == '.') {
                return seq;
            }
            if (bp <= 0) {
                return null;
            }
            Point chosen = null;
            for (Point p : blackFightMoves(state, tr, tc, approach)) {
                Board afterBlack = state.copy();
                if (afterBlack.play('X', p) == null) {
                    continue;
                }
                if (afterBlack.get(tr, tc) == '.') {
                    chosen = p;
                    break;
                }
                boolean ok = true;
                List<Point> replies = new ArrayList<>();
                replies.add(null);
                replies.addAll(whiteFightMoves(afterBlack, tr, tc));
                for (Point opt : replies) {
                    Board afterWhite = afterBlack.copy();
                    if (opt == null) {
                        afterWhite.play('O', null);
                    } else if (afterWhite.play('O', opt) == null) {
                        continue;
                    }
                    if (!blackCanForce(afterWhite, tr, tc, bp - 1, approach)) {
                        ok = false;
                        break;
                    }
                }
                if (ok) {
                    chosen = p;
                    break;
                }
            }
            if (chosen == null) {
                return null;
            }
            state.play('X', chosen);
            seq.add("black " + chosen.r + "," + chosen.c);
            bp--;
            if (state.get(tr, tc) == '.') {
                return seq;
            }
            boolean foundReply = false;
            Point wchoice = null;
            List<Point> options = new ArrayList<>(whiteFightMoves(state, tr, tc));
            options.add(null);
            for (Point opt : options) {
                Board after = state.copy();
                if (opt == null) {
                    after.play('O', null);
                } else if (after.play('O', opt) == null) {
                    continue;
                }
                if (blackCanForce(after, tr, tc, bp, approach)) {
                    wchoice = opt;
                    foundReply = true;
                    break;
                }
            }
            if (!foundReply) {
                return null;
            }
            if (wchoice == null) {
                state.play('O', null);
                seq.add("white pass");
            } else {
                state.play('O', wchoice);
                seq.add("white " + wchoice.r + "," + wchoice.c);
            }
        }
        return null;
    }

    private static boolean blackCanForce(Board root, int tr, int tc, int maxBlack, boolean approach) {
        Map<String, Boolean> memo = new HashMap<>();
        return blackToPlay(root, tr, tc, maxBlack, maxBlack * 2 + 4, approach, memo);
    }

    private static boolean blackToPlay(
            Board state, int tr, int tc, int bp, int depth, boolean approach, Map<String, Boolean> memo) {
        String key = "B|" + state.key() + "|" + bp + "|" + depth + "|" + (approach ? 1 : 0);
        Boolean cached = memo.get(key);
        if (cached != null) {
            return cached;
        }
        if (state.get(tr, tc) == '.') {
            memo.put(key, true);
            return true;
        }
        if (bp <= 0 || depth <= 0) {
            memo.put(key, false);
            return false;
        }
        for (Point p : blackFightMoves(state, tr, tc, approach)) {
            Board next = state.copy();
            if (next.play('X', p) == null) {
                continue;
            }
            if (next.get(tr, tc) == '.' || whiteToPlay(next, tr, tc, bp - 1, depth - 1, approach, memo)) {
                memo.put(key, true);
                return true;
            }
        }
        memo.put(key, false);
        return false;
    }

    private static boolean whiteToPlay(
            Board state, int tr, int tc, int bp, int depth, boolean approach, Map<String, Boolean> memo) {
        String key = "W|" + state.key() + "|" + bp + "|" + depth + "|" + (approach ? 1 : 0);
        Boolean cached = memo.get(key);
        if (cached != null) {
            return cached;
        }
        if (state.get(tr, tc) == '.') {
            memo.put(key, true);
            return true;
        }
        if (depth <= 0) {
            memo.put(key, false);
            return false;
        }
        List<Point> options = new ArrayList<>();
        options.add(null);
        options.addAll(whiteFightMoves(state, tr, tc));
        for (Point opt : options) {
            Board next = state.copy();
            if (opt == null) {
                next.play('O', null);
            } else if (next.play('O', opt) == null) {
                continue;
            }
            if (!blackToPlay(next, tr, tc, bp, depth - 1, approach, memo)) {
                memo.put(key, false);
                return false;
            }
        }
        memo.put(key, true);
        return true;
    }

    private static List<Point> blackFightMoves(Board b, int tr, int tc, boolean approach) {
        Set<Point> seen = new HashSet<>();
        List<Point> out = new ArrayList<>();
        if (b.get(tr, tc) == '.') {
            return out;
        }
        for (Point p : sorted(b.groupLibs(tr, tc))) {
            if (seen.add(p)) {
                out.add(p);
            }
            if (!approach) {
                continue;
            }
            for (int i = 0; i < 4; i++) {
                int nr = p.r + DR[i];
                int nc = p.c + DC[i];
                if (!b.inb(nr, nc) || b.get(nr, nc) != '.') {
                    continue;
                }
                Point seal = new Point(nr, nc);
                if (seen.add(seal)) {
                    out.add(seal);
                }
            }
        }
        if (!approach) {
            return out;
        }
        for (int r = 1; r <= N; r++) {
            for (int c = 1; c <= N; c++) {
                if (b.get(r, c) != '.') {
                    continue;
                }
                Point p = new Point(r, c);
                int dist = Math.max(Math.abs(r - tr), Math.abs(c - tc));
                if (dist > 5) {
                    continue;
                }
                Board n = b.copy();
                Integer caps = n.play('X', p);
                if (caps == null) {
                    continue;
                }
                boolean useful = caps > 0;
                if (!useful) {
                    for (int i = 0; i < 4; i++) {
                        int nr = r + DR[i];
                        int nc = c + DC[i];
                        if (b.inb(nr, nc) && b.get(nr, nc) == 'X') {
                            useful = true;
                            break;
                        }
                    }
                }
                if (useful && seen.add(p)) {
                    out.add(p);
                }
            }
        }
        out.sort((a, c) -> a.r != c.r ? Integer.compare(a.r, c.r) : Integer.compare(a.c, c.c));
        return out;
    }

    /** Liberty + atari replies for White (refutations and resistance). */
    private static List<Point> whiteFightMoves(Board b, int tr, int tc) {
        List<Point> out = new ArrayList<>();
        Set<Point> seen = new HashSet<>();
        if (b.get(tr, tc) == '.') {
            return out;
        }
        for (Point p : sorted(b.groupLibs(tr, tc))) {
            Board n = b.copy();
            if (n.play('O', p) == null) {
                continue;
            }
            out.add(p);
            seen.add(p);
        }
        for (int r = 1; r <= N; r++) {
            for (int c = 1; c <= N; c++) {
                if (b.get(r, c) != 'X') {
                    continue;
                }
                Set<Point> libs = b.groupLibs(r, c);
                if (libs.size() != 1) {
                    continue;
                }
                Point lib = libs.iterator().next();
                if (seen.contains(lib)) {
                    continue;
                }
                Board n = b.copy();
                if (n.play('O', lib) != null) {
                    out.add(lib);
                    seen.add(lib);
                }
            }
        }
        return out;
    }

    private static List<Point> sorted(Set<Point> pts) {
        List<Point> list = new ArrayList<>(pts);
        list.sort((a, b) -> a.r != b.r ? Integer.compare(a.r, b.r) : Integer.compare(a.c, b.c));
        return list;
    }

    private static RefResult validateJar(Path board, List<String> moves) throws Exception {
        List<String> cmd = new ArrayList<>();
        cmd.add("java");
        cmd.add("-jar");
        cmd.add(REFEREE.toString());
        cmd.add("validate");
        cmd.add("--board");
        cmd.add(board.toString());
        cmd.add("--moves");
        cmd.add(String.join(";", moves));
        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.redirectErrorStream(true);
        Process proc = pb.start();
        String stdout;
        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(proc.getInputStream(), StandardCharsets.UTF_8))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                if (sb.length() > 0) {
                    sb.append('\n');
                }
                sb.append(line);
            }
            stdout = sb.toString();
        }
        int rc = proc.waitFor();
        if (rc != 0 || stdout.isBlank()) {
            throw new IllegalStateException("referee failed rc=" + rc + " out=" + stdout);
        }
        boolean allLegal = stdout.contains("\"all_legal\": true") || stdout.contains("\"all_legal\":true");
        boolean targetEmpty = stdout.contains("\"target_empty\": true") || stdout.contains("\"target_empty\":true");
        return new RefResult(allLegal, targetEmpty);
    }

    private static final class RefResult {
        final boolean allLegal;
        final boolean targetEmpty;

        RefResult(boolean allLegal, boolean targetEmpty) {
            this.allLegal = allLegal;
            this.targetEmpty = targetEmpty;
        }
    }

    private static final class Point {
        final int r;
        final int c;

        Point(int r, int c) {
            this.r = r;
            this.c = c;
        }

        @Override
        public boolean equals(Object o) {
            if (!(o instanceof Point)) {
                return false;
            }
            Point p = (Point) o;
            return r == p.r && c == p.c;
        }

        @Override
        public int hashCode() {
            return Objects.hash(r, c);
        }
    }

    private static final class Puzzle {
        final int id;
        final String toMove;
        final int tr;
        final int tc;
        final Board board;

        Puzzle(int id, String toMove, int tr, int tc, Board board) {
            this.id = id;
            this.toMove = toMove;
            this.tr = tr;
            this.tc = tc;
            this.board = board;
        }

        static Puzzle load(Path path) throws IOException {
            int id = 0;
            String toMove = "black";
            int tr = 1;
            int tc = 1;
            List<String> rows = new ArrayList<>();
            boolean inBoard = false;
            for (String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
                if (line.startsWith("puzzle_id:")) {
                    id = Integer.parseInt(line.substring("puzzle_id:".length()).trim());
                } else if (line.startsWith("to_move:")) {
                    toMove = line.substring("to_move:".length()).trim();
                } else if (line.startsWith("target:")) {
                    String[] rc = line.substring("target:".length()).trim().split(",");
                    tr = Integer.parseInt(rc[0].trim());
                    tc = Integer.parseInt(rc[1].trim());
                } else if (line.startsWith("board:")) {
                    inBoard = true;
                } else if (inBoard) {
                    String row = line.trim();
                    if (row.length() == N) {
                        rows.add(row);
                    }
                }
            }
            if (rows.size() != N) {
                throw new IllegalStateException("bad board rows in " + path);
            }
            return new Puzzle(id, toMove, tr, tc, Board.fromRows(rows));
        }
    }

    private static final class Board {
        private final char[][] g;

        private Board(char[][] g) {
            this.g = g;
        }

        static Board fromRows(List<String> rows) {
            char[][] g = new char[N][N];
            for (int r = 0; r < N; r++) {
                g[r] = rows.get(r).toCharArray();
            }
            return new Board(g);
        }

        Board copy() {
            char[][] n = new char[N][N];
            for (int r = 0; r < N; r++) {
                n[r] = Arrays.copyOf(g[r], N);
            }
            return new Board(n);
        }

        char get(int r, int c) {
            return g[r - 1][c - 1];
        }

        void set(int r, int c, char v) {
            g[r - 1][c - 1] = v;
        }

        boolean inb(int r, int c) {
            return r >= 1 && r <= N && c >= 1 && c <= N;
        }

        String key() {
            StringBuilder sb = new StringBuilder(N * N);
            for (int r = 0; r < N; r++) {
                sb.append(g[r]);
            }
            return sb.toString();
        }

        Set<Point> groupLibs(int sr, int sc) {
            char color = get(sr, sc);
            if (color == '.') {
                return Set.of();
            }
            Set<Point> stones = new HashSet<>();
            Set<Point> libs = new HashSet<>();
            ArrayDeque<Point> q = new ArrayDeque<>();
            q.add(new Point(sr, sc));
            stones.add(new Point(sr, sc));
            while (!q.isEmpty()) {
                Point p = q.removeFirst();
                for (int i = 0; i < 4; i++) {
                    int nr = p.r + DR[i];
                    int nc = p.c + DC[i];
                    if (!inb(nr, nc)) {
                        continue;
                    }
                    char cell = get(nr, nc);
                    Point np = new Point(nr, nc);
                    if (cell == color) {
                        if (stones.add(np)) {
                            q.add(np);
                        }
                    } else if (cell == '.') {
                        libs.add(np);
                    }
                }
            }
            return libs;
        }

        private Set<Point> groupStones(int sr, int sc) {
            char color = get(sr, sc);
            Set<Point> stones = new HashSet<>();
            ArrayDeque<Point> q = new ArrayDeque<>();
            q.add(new Point(sr, sc));
            stones.add(new Point(sr, sc));
            while (!q.isEmpty()) {
                Point p = q.removeFirst();
                for (int i = 0; i < 4; i++) {
                    int nr = p.r + DR[i];
                    int nc = p.c + DC[i];
                    if (!inb(nr, nc)) {
                        continue;
                    }
                    if (get(nr, nc) == color) {
                        Point np = new Point(nr, nc);
                        if (stones.add(np)) {
                            q.add(np);
                        }
                    }
                }
            }
            return stones;
        }

        /** Play colour X/O at point, or pass when move is null. Returns captures, or null if illegal. */
        Integer play(char color, Point move) {
            if (move == null) {
                return 0;
            }
            if (get(move.r, move.c) != '.') {
                return null;
            }
            char opp = color == 'X' ? 'O' : 'X';
            set(move.r, move.c, color);
            int caps = 0;
            for (int i = 0; i < 4; i++) {
                int nr = move.r + DR[i];
                int nc = move.c + DC[i];
                if (!inb(nr, nc) || get(nr, nc) != opp) {
                    continue;
                }
                if (groupLibs(nr, nc).isEmpty()) {
                    Set<Point> dead = groupStones(nr, nc);
                    for (Point d : dead) {
                        set(d.r, d.c, '.');
                    }
                    caps += dead.size();
                }
            }
            if (groupLibs(move.r, move.c).isEmpty() && caps == 0) {
                set(move.r, move.c, '.');
                return null;
            }
            return caps;
        }
    }
}
