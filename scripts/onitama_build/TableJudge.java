import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Sealed table judge for the Onitama temple-path puzzle sheets.
 *
 * Coordinate system: files a..e (0..4), ranks 1..5 (rows 0..4). Sensei sits
 * on the low ranks; Pupil sits on the high ranks. Sheet board lines are
 * listed rank 1 first (row 0) through rank 5 last (row 4). Sensei temple is
 * c1; Pupil temple is c5. Card offsets are stamp-relative for Sensei;
 * Pupil applies the same offsets with both signs flipped.
 */
public final class TableJudge {

    private static final int N = 5;
    private static final int SENSEI = 0;
    private static final int PUPIL = 1;
    private static final int EMPTY = 0;

    private static final Map<String, int[][]> CARDS = new LinkedHashMap<>();

    static {
        CARDS.put("Tiger", new int[][] {{0, 2}, {0, -1}});
        CARDS.put("Dragon", new int[][] {{-2, 1}, {2, 1}, {-1, -1}, {1, -1}});
        CARDS.put("Frog", new int[][] {{-2, 0}, {-1, 1}, {1, -1}});
        CARDS.put("Rabbit", new int[][] {{1, 1}, {2, 0}, {-1, -1}});
        CARDS.put("Crab", new int[][] {{-2, 0}, {2, 0}, {0, 1}});
        CARDS.put("Elephant", new int[][] {{-1, 0}, {1, 0}, {-1, 1}, {1, 1}});
        CARDS.put("Goose", new int[][] {{-1, 0}, {-1, 1}, {1, 0}, {1, -1}});
        CARDS.put("Rooster", new int[][] {{-1, 0}, {-1, -1}, {1, 0}, {1, 1}});
        CARDS.put("Monkey", new int[][] {{-1, 1}, {1, 1}, {-1, -1}, {1, -1}});
        CARDS.put("Mantis", new int[][] {{-1, 1}, {1, 1}, {0, -1}});
        CARDS.put("Horse", new int[][] {{-1, 0}, {0, 1}, {0, -1}});
        CARDS.put("Ox", new int[][] {{1, 0}, {0, 1}, {0, -1}});
        CARDS.put("Crane", new int[][] {{-1, -1}, {1, -1}, {0, 1}});
        CARDS.put("Boar", new int[][] {{-1, 0}, {1, 0}, {0, 1}});
        CARDS.put("Eel", new int[][] {{-1, 1}, {-1, -1}, {1, 0}});
        CARDS.put("Cobra", new int[][] {{1, 1}, {1, -1}, {-1, 0}});
    }

    private TableJudge() {
    }

    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("usage: TableJudge <view|legal|apply|validate> --board <sheet> ...");
            System.exit(2);
            return;
        }
        try {
            String verb = args[0];
            Map<String, String> opts = parseOpts(args, 1);
            switch (verb) {
                case "view":
                    cmdView(opts);
                    break;
                case "legal":
                    cmdLegal(opts);
                    break;
                case "apply":
                    cmdApply(opts);
                    break;
                case "validate":
                    cmdValidate(opts);
                    break;
                default:
                    System.err.println("unknown verb: " + verb);
                    System.exit(2);
            }
        } catch (Exception e) {
            System.err.println("error: " + e.getMessage());
            System.exit(1);
        }
    }

    // ------------------------------------------------------------------
    // CLI option parsing
    // ------------------------------------------------------------------

    private static Map<String, String> parseOpts(String[] args, int start) {
        Map<String, String> out = new LinkedHashMap<>();
        int i = start;
        while (i < args.length) {
            String tok = args[i];
            if (tok.startsWith("--")) {
                String key = tok.substring(2);
                if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
                    out.put(key, args[i + 1]);
                    i += 2;
                } else {
                    out.put(key, "true");
                    i += 1;
                }
            } else {
                i += 1;
            }
        }
        return out;
    }

    private static String require(Map<String, String> opts, String key) {
        String v = opts.get(key);
        if (v == null) {
            throw new IllegalArgumentException("missing --" + key);
        }
        return v;
    }

    private static Path requirePath(Map<String, String> opts, String key) {
        return Paths.get(require(opts, key));
    }

    // ------------------------------------------------------------------
    // Position model
    // ------------------------------------------------------------------

    private static final class Pos {
        int[] cells;
        String[] senseiCards;
        String[] pupilCards;
        String sideboard;
        int toMove;
        int budget;
        String boardId;

        Pos copy() {
            Pos p = new Pos();
            p.cells = cells.clone();
            p.senseiCards = senseiCards.clone();
            p.pupilCards = pupilCards.clone();
            p.sideboard = sideboard;
            p.toMove = toMove;
            p.budget = budget;
            p.boardId = boardId;
            return p;
        }
    }

    private static final class Move {
        final String card;
        final int ff;
        final int fr;
        final int tf;
        final int tr;

        Move(String card, int ff, int fr, int tf, int tr) {
            this.card = card;
            this.ff = ff;
            this.fr = fr;
            this.tf = tf;
            this.tr = tr;
        }

        boolean matches(Move other) {
            return card.equals(other.card) && ff == other.ff && fr == other.fr
                    && tf == other.tf && tr == other.tr;
        }
    }

    private static int idx(int f, int r) {
        return r * N + f;
    }

    private static boolean inBounds(int f, int r) {
        return f >= 0 && f < N && r >= 0 && r < N;
    }

    private static String sqName(int f, int r) {
        return "" + (char) ('a' + f) + (r + 1);
    }

    private static int[] parseSq(String token) {
        String t = token.trim().toLowerCase();
        int f = t.charAt(0) - 'a';
        int r = Integer.parseInt(t.substring(1)) - 1;
        return new int[] {f, r};
    }

    // ------------------------------------------------------------------
    // Sheet reading
    // ------------------------------------------------------------------

    private static Pos readSheet(Path path) throws IOException {
        List<String> lines = Files.readAllLines(path);
        Map<String, String> meta = new LinkedHashMap<>();
        List<String> boardLines = new ArrayList<>();
        boolean inBoard = false;
        for (String raw : lines) {
            String line = raw.stripTrailing();
            if (line.isEmpty() || line.startsWith("#")) {
                continue;
            }
            if (line.startsWith("board:")) {
                inBoard = true;
                continue;
            }
            if (inBoard) {
                boardLines.add(line.trim());
                continue;
            }
            int c = line.indexOf(':');
            if (c >= 0) {
                meta.put(line.substring(0, c).trim(), line.substring(c + 1).trim());
            }
        }
        if (boardLines.size() != N) {
            throw new IllegalArgumentException("bad board rows in " + path + ": " + boardLines.size());
        }
        int[] cells = new int[N * N];
        for (int r = 0; r < N; r++) {
            String row = boardLines.get(r);
            if (row.length() != N) {
                throw new IllegalArgumentException("bad board width in " + path + ": " + row);
            }
            for (int f = 0; f < N; f++) {
                char ch = row.charAt(f);
                int v;
                switch (ch) {
                    case '.':
                        v = EMPTY;
                        break;
                    case 's':
                        v = 1;
                        break;
                    case 'S':
                        v = 2;
                        break;
                    case 'p':
                        v = -1;
                        break;
                    case 'P':
                        v = -2;
                        break;
                    default:
                        throw new IllegalArgumentException("bad cell " + ch + " in " + path);
                }
                cells[idx(f, r)] = v;
            }
        }
        String[] sc = splitCards(meta.get("sensei_cards"), path);
        String[] pc = splitCards(meta.get("pupil_cards"), path);
        Pos pos = new Pos();
        pos.cells = cells;
        pos.senseiCards = sc;
        pos.pupilCards = pc;
        pos.sideboard = meta.getOrDefault("sideboard", "").trim();
        String tm = meta.getOrDefault("to_move", "sensei").trim().toLowerCase();
        pos.toMove = tm.equals("sensei") ? SENSEI : PUPIL;
        pos.budget = Integer.parseInt(meta.getOrDefault("mate_budget", "3").trim());
        pos.boardId = meta.getOrDefault("board_id", "").trim();
        return pos;
    }

    private static String[] splitCards(String raw, Path path) {
        if (raw == null) {
            throw new IllegalArgumentException("missing card hand in " + path);
        }
        String[] parts = raw.split(",");
        if (parts.length != 2) {
            throw new IllegalArgumentException("need two cards per hand in " + path);
        }
        return new String[] {parts[0].trim(), parts[1].trim()};
    }

    // ------------------------------------------------------------------
    // Rules
    // ------------------------------------------------------------------

    private static String[] handOf(Pos pos, int who) {
        return who == SENSEI ? pos.senseiCards : pos.pupilCards;
    }

    private static int[][] offsetsFor(String card, int who) {
        int[][] raw = CARDS.get(card);
        if (raw == null) {
            throw new IllegalArgumentException("unknown card: " + card);
        }
        if (who == SENSEI) {
            return raw;
        }
        int[][] flipped = new int[raw.length][2];
        for (int i = 0; i < raw.length; i++) {
            flipped[i][0] = -raw[i][0];
            flipped[i][1] = -raw[i][1];
        }
        return flipped;
    }

    private static int[] masterSq(Pos pos, int who) {
        int want = who == SENSEI ? 2 : -2;
        for (int r = 0; r < N; r++) {
            for (int f = 0; f < N; f++) {
                if (pos.cells[idx(f, r)] == want) {
                    return new int[] {f, r};
                }
            }
        }
        return null;
    }

    private static int[] temple(int who) {
        return who == SENSEI ? new int[] {2, 0} : new int[] {2, 4};
    }

    private static Integer winner(Pos pos) {
        int[] sm = masterSq(pos, SENSEI);
        int[] pm = masterSq(pos, PUPIL);
        if (sm == null) {
            return PUPIL;
        }
        if (pm == null) {
            return SENSEI;
        }
        int[] pupilTemple = temple(PUPIL);
        int[] senseiTemple = temple(SENSEI);
        if (sm[0] == pupilTemple[0] && sm[1] == pupilTemple[1]) {
            return SENSEI;
        }
        if (pm[0] == senseiTemple[0] && pm[1] == senseiTemple[1]) {
            return PUPIL;
        }
        return null;
    }

    private static List<Move> legalMoves(Pos pos) {
        List<Move> moves = new ArrayList<>();
        if (winner(pos) != null) {
            return moves;
        }
        int who = pos.toMove;
        String[] hand = handOf(pos, who);
        int ownStudent = who == SENSEI ? 1 : -1;
        int ownMaster = who == SENSEI ? 2 : -2;
        for (String card : hand) {
            int[][] offs = offsetsFor(card, who);
            for (int r = 0; r < N; r++) {
                for (int f = 0; f < N; f++) {
                    int p = pos.cells[idx(f, r)];
                    if (p != ownStudent && p != ownMaster) {
                        continue;
                    }
                    for (int[] d : offs) {
                        int tf = f + d[0];
                        int tr = r + d[1];
                        if (!inBounds(tf, tr)) {
                            continue;
                        }
                        int dest = pos.cells[idx(tf, tr)];
                        if (who == SENSEI && dest > 0) {
                            continue;
                        }
                        if (who == PUPIL && dest < 0) {
                            continue;
                        }
                        moves.add(new Move(card, f, r, tf, tr));
                    }
                }
            }
        }
        return moves;
    }

    private static Pos applyMove(Pos pos, Move move) {
        int who = pos.toMove;
        int[] cells = pos.cells.clone();
        int piece = cells[idx(move.ff, move.fr)];
        cells[idx(move.ff, move.fr)] = EMPTY;
        cells[idx(move.tf, move.tr)] = piece;

        List<String> hand = new ArrayList<>(Arrays.asList(handOf(pos, who)));
        if (!hand.remove(move.card)) {
            throw new IllegalStateException("card " + move.card + " not in hand " + hand);
        }
        String gained = pos.sideboard;
        hand.add(gained);
        String[] handArr = hand.toArray(new String[0]);

        Pos next = new Pos();
        next.cells = cells;
        next.sideboard = move.card;
        next.toMove = 1 - who;
        next.budget = pos.budget;
        next.boardId = pos.boardId;
        if (who == SENSEI) {
            next.senseiCards = handArr;
            next.pupilCards = pos.pupilCards.clone();
        } else {
            next.senseiCards = pos.senseiCards.clone();
            next.pupilCards = handArr;
        }
        return next;
    }

    private static String moveToken(Move m, Integer who) {
        String body = m.card + ":" + sqName(m.ff, m.fr) + "-" + sqName(m.tf, m.tr);
        if (who == null) {
            return body;
        }
        String side = who == SENSEI ? "sensei" : "pupil";
        return side + " " + body;
    }

    private static Object[] parseMoveToken(String token) {
        String t = token.trim();
        int who;
        String rest;
        int sp = t.indexOf(' ');
        if (sp >= 0) {
            String sideS = t.substring(0, sp).trim();
            rest = t.substring(sp + 1).trim();
            who = sideS.equals("sensei") ? SENSEI : PUPIL;
        } else {
            who = SENSEI;
            rest = t;
        }
        int colon = rest.indexOf(':');
        if (colon < 0) {
            throw new IllegalArgumentException("bad move token: " + token);
        }
        String card = rest.substring(0, colon).trim();
        String path = rest.substring(colon + 1).trim();
        int dash = path.indexOf('-');
        if (dash < 0) {
            throw new IllegalArgumentException("bad move token: " + token);
        }
        int[] from = parseSq(path.substring(0, dash));
        int[] to = parseSq(path.substring(dash + 1));
        return new Object[] {who, card, from[0], from[1], to[0], to[1]};
    }

    // ------------------------------------------------------------------
    // Verbs
    // ------------------------------------------------------------------

    private static void cmdView(Map<String, String> opts) throws IOException {
        Pos pos = readSheet(requirePath(opts, "board"));
        StringBuilder sb = new StringBuilder();
        sb.append("board_id: ").append(pos.boardId).append('\n');
        sb.append("to_move: ").append(pos.toMove == SENSEI ? "sensei" : "pupil").append('\n');
        sb.append("mate_budget: ").append(pos.budget).append('\n');
        sb.append("sensei_cards: ").append(String.join(",", pos.senseiCards)).append('\n');
        sb.append("pupil_cards: ").append(String.join(",", pos.pupilCards)).append('\n');
        sb.append("sideboard: ").append(pos.sideboard).append('\n');
        sb.append("board:\n");
        appendBoard(sb, pos);
        sb.append("temples: sensei=").append(sqName(2, 0)).append(" pupil=").append(sqName(2, 4)).append('\n');
        System.out.print(sb);
    }

    private static void cmdLegal(Map<String, String> opts) throws IOException {
        Pos pos = readSheet(requirePath(opts, "board"));
        String sideS = require(opts, "side").trim().toLowerCase();
        int side;
        if (sideS.equals("sensei")) {
            side = SENSEI;
        } else if (sideS.equals("pupil")) {
            side = PUPIL;
        } else {
            throw new IllegalArgumentException("side must be sensei or pupil");
        }
        Pos probe = pos.copy();
        probe.toMove = side;
        List<Move> moves = legalMoves(probe);
        List<String> tokens = new ArrayList<>();
        for (Move m : moves) {
            tokens.add(moveToken(m, side));
        }
        Collections.sort(tokens);
        StringBuilder sb = new StringBuilder();
        for (String t : tokens) {
            sb.append(t).append('\n');
        }
        System.out.print(sb);
    }

    private static void cmdApply(Map<String, String> opts) throws IOException {
        Pos pos = readSheet(requirePath(opts, "board"));
        String moveTok = require(opts, "move");
        Object[] parsed = parseMoveToken(moveTok);
        int who = (int) parsed[0];
        Move target = new Move((String) parsed[1], (int) parsed[2], (int) parsed[3],
                (int) parsed[4], (int) parsed[5]);
        if (who != pos.toMove) {
            System.out.println("illegal: side mismatch, to_move is "
                    + (pos.toMove == SENSEI ? "sensei" : "pupil"));
            System.exit(1);
            return;
        }
        Move found = null;
        for (Move m : legalMoves(pos)) {
            if (m.matches(target)) {
                found = m;
                break;
            }
        }
        if (found == null) {
            System.out.println("illegal: move not in legal set");
            System.exit(1);
            return;
        }
        Pos next = applyMove(pos, found);
        Integer w = winner(next);
        StringBuilder sb = new StringBuilder();
        sb.append("applied: ").append(moveTok).append('\n');
        sb.append("to_move: ").append(next.toMove == SENSEI ? "sensei" : "pupil").append('\n');
        sb.append("sensei_cards: ").append(String.join(",", next.senseiCards)).append('\n');
        sb.append("pupil_cards: ").append(String.join(",", next.pupilCards)).append('\n');
        sb.append("sideboard: ").append(next.sideboard).append('\n');
        sb.append("winner: ").append(w == null ? "none" : (w == SENSEI ? "sensei" : "pupil")).append('\n');
        sb.append("board:\n");
        appendBoard(sb, next);
        System.out.print(sb);
    }

    private static void cmdValidate(Map<String, String> opts) throws IOException {
        Pos pos = readSheet(requirePath(opts, "board"));
        String line = require(opts, "line");
        boolean coop = opts.containsKey("coop");

        String trimmed = line.trim();
        String[] toks = trimmed.isEmpty() ? new String[0] : trimmed.split(";");

        boolean allLegal = true;
        int senseiPlies = 0;
        List<String> sideboards = new ArrayList<>();
        Pos cur = pos;
        Integer w = winner(cur);

        for (String rawTok : toks) {
            String tok = rawTok.trim();
            if (tok.isEmpty()) {
                continue;
            }
            if (w != null) {
                allLegal = false;
                break;
            }
            Object[] parsed = parseMoveToken(tok);
            int who = (int) parsed[0];
            Move target = new Move((String) parsed[1], (int) parsed[2], (int) parsed[3],
                    (int) parsed[4], (int) parsed[5]);
            if (who != cur.toMove) {
                allLegal = false;
                break;
            }
            Move found = null;
            for (Move m : legalMoves(cur)) {
                if (m.matches(target)) {
                    found = m;
                    break;
                }
            }
            if (found == null) {
                allLegal = false;
                break;
            }
            Pos next = applyMove(cur, found);
            if (who == SENSEI) {
                senseiPlies++;
            }
            sideboards.add(next.sideboard);
            Integer nw = winner(next);
            if (coop && who == SENSEI && nw == null && next.toMove == PUPIL) {
                next.toMove = SENSEI;
            }
            cur = next;
            w = nw;
        }

        int[] sm = masterSq(cur, SENSEI);
        int[] pm = masterSq(cur, PUPIL);
        int[] pupilTemple = temple(PUPIL);
        boolean templeReached = sm != null && sm[0] == pupilTemple[0] && sm[1] == pupilTemple[1];
        boolean masterCapture = sm == null || pm == null;
        String winnerStr = w == null ? "none" : (w == SENSEI ? "sensei" : "pupil");

        StringBuilder json = new StringBuilder();
        json.append('{');
        json.append("\"all_legal\":").append(allLegal).append(',');
        json.append("\"sensei_plies\":").append(senseiPlies).append(',');
        json.append("\"temple\":").append(templeReached).append(',');
        json.append("\"master_capture\":").append(masterCapture).append(',');
        json.append("\"winner\":\"").append(jsonEscape(winnerStr)).append("\",");
        json.append("\"sideboards\":[");
        for (int i = 0; i < sideboards.size(); i++) {
            if (i > 0) {
                json.append(',');
            }
            json.append('"').append(jsonEscape(sideboards.get(i))).append('"');
        }
        json.append(']');
        json.append('}');
        System.out.println(json);
    }

    private static void appendBoard(StringBuilder sb, Pos pos) {
        for (int r = 0; r < N; r++) {
            for (int f = 0; f < N; f++) {
                int v = pos.cells[idx(f, r)];
                char ch;
                switch (v) {
                    case 1:
                        ch = 's';
                        break;
                    case 2:
                        ch = 'S';
                        break;
                    case -1:
                        ch = 'p';
                        break;
                    case -2:
                        ch = 'P';
                        break;
                    default:
                        ch = '.';
                        break;
                }
                sb.append(ch);
            }
            sb.append('\n');
        }
    }

    private static String jsonEscape(String s) {
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"' || c == '\\') {
                out.append('\\').append(c);
            } else if (c == '\n') {
                out.append("\\n");
            } else {
                out.append(c);
            }
        }
        return out.toString();
    }
}
