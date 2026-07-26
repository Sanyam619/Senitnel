package io.terminus.stitch.util;

/**
 * SplitMix64 PRNG. Deterministic, fast, well-mixed, and independent of the
 * JDK's own random stream so the generated dataset is stable across Java
 * versions and platforms.
 */
public final class Prng {
    private long state;

    public Prng(long seed) {
        this.state = seed == 0L ? 0x9E3779B97F4A7C15L : seed;
    }

    public long nextLong() {
        state += 0x9E3779B97F4A7C15L;
        long z = state;
        z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
        z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
        return z ^ (z >>> 31);
    }

    /** Uniform double in [-1, 1). */
    public double nextUniform() {
        long bits = nextLong() >>> 11;
        double u = bits / (double) (1L << 53);
        return 2.0 * u - 1.0;
    }

    /** Approximate standard normal via 12-uniform sum (mean 0, var 1). */
    public double nextGaussian() {
        double s = 0.0;
        for (int i = 0; i < 12; i++) {
            s += nextUniform();
        }
        // Sum of 12 uniforms on [-1,1) has variance 12 * (1/3) = 4, so divide by 2.
        return s * 0.5;
    }
}
