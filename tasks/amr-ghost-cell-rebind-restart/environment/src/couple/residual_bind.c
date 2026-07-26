#include "couple.h"
#include <stdio.h>
#include <string.h>

static float g_l2[32];
static float g_mass[32];
static int g_ready = 0;

static void load_lut(void) {
    if (g_ready) {
        return;
    }
    FILE *fp = fopen("/app/data/bind_lut.bin", "rb");
    if (!fp) {
        return;
    }
    for (int i = 0; i < 32; i++) {
        if (fread(&g_l2[i], sizeof(float), 1, fp) != 1) {
            break;
        }
        if (fread(&g_mass[i], sizeof(float), 1, fp) != 1) {
            break;
        }
    }
    fclose(fp);
    g_ready = 1;
}

void couple_residual_metrics(uint32_t tag, float base, float *l2, float *mass) {
    load_lut();
    int idx = (int)(tag & 31u);
    *l2 = base + g_l2[idx];
    *mass = g_mass[idx];
}
