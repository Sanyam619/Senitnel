package io.terminus.stitch.util;

/** Row-major dense matrix helpers used throughout the pipeline. */
public final class MatOps {
    private MatOps() {}

    public static double[][] zeros(int rows, int cols) {
        return new double[rows][cols];
    }

    public static double[][] copy(double[][] m) {
        double[][] c = new double[m.length][];
        for (int i = 0; i < m.length; i++) {
            c[i] = m[i].clone();
        }
        return c;
    }

    /** out = A x B where A is (m,k) and B is (k,n). */
    public static double[][] mul(double[][] a, double[][] b) {
        int m = a.length;
        int k = a[0].length;
        int n = b[0].length;
        if (b.length != k) {
            throw new IllegalArgumentException("mul: inner dim mismatch " + k + " vs " + b.length);
        }
        double[][] out = new double[m][n];
        for (int i = 0; i < m; i++) {
            double[] ai = a[i];
            double[] outi = out[i];
            for (int p = 0; p < k; p++) {
                double aip = ai[p];
                if (aip == 0.0) continue;
                double[] bp = b[p];
                for (int j = 0; j < n; j++) {
                    outi[j] += aip * bp[j];
                }
            }
        }
        return out;
    }

    /** out = A + s * B in place on A. */
    public static void axpy(double[][] a, double s, double[][] b) {
        for (int i = 0; i < a.length; i++) {
            double[] ai = a[i];
            double[] bi = b[i];
            for (int j = 0; j < ai.length; j++) {
                ai[j] += s * bi[j];
            }
        }
    }

    /** out = a - b. */
    public static double[][] sub(double[][] a, double[][] b) {
        double[][] out = new double[a.length][a[0].length];
        for (int i = 0; i < a.length; i++) {
            for (int j = 0; j < a[0].length; j++) {
                out[i][j] = a[i][j] - b[i][j];
            }
        }
        return out;
    }

    /** In place scale a *= s. */
    public static void scaleInPlace(double[][] a, double s) {
        for (int i = 0; i < a.length; i++) {
            double[] ai = a[i];
            for (int j = 0; j < ai.length; j++) {
                ai[j] *= s;
            }
        }
    }

    /** Return a new matrix = s * a. */
    public static double[][] scaled(double[][] a, double s) {
        double[][] out = copy(a);
        scaleInPlace(out, s);
        return out;
    }

    /** Frobenius norm sqrt(sum a[i][j]^2). */
    public static double frobenius(double[][] a) {
        double s = 0.0;
        for (int i = 0; i < a.length; i++) {
            double[] ai = a[i];
            for (int j = 0; j < ai.length; j++) {
                s += ai[j] * ai[j];
            }
        }
        return Math.sqrt(s);
    }

    /** Square of Frobenius (avoids sqrt for accumulation). */
    public static double frobeniusSquared(double[][] a) {
        double s = 0.0;
        for (int i = 0; i < a.length; i++) {
            double[] ai = a[i];
            for (int j = 0; j < ai.length; j++) {
                s += ai[j] * ai[j];
            }
        }
        return s;
    }

    /**
     * Return a resized copy of `m` with `newRows` rows and the same column count.
     * If newRows > m.rows, the extra rows are zero.
     * If newRows < m.rows, the extra rows are dropped.
     */
    public static double[][] resizeRows(double[][] m, int newRows) {
        int cols = m[0].length;
        double[][] out = new double[newRows][cols];
        int copyRows = Math.min(newRows, m.length);
        for (int i = 0; i < copyRows; i++) {
            System.arraycopy(m[i], 0, out[i], 0, cols);
        }
        return out;
    }
}
