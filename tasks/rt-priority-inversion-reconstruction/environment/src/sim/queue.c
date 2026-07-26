#include <string.h>

int klb_pick_runnable(const char *running, const char actors[][32], const int prios[], int n, const int effective[]) {
    int best = -1;
    int bestp = -1;
    for (int i = 0; i < n; i++) {
        int p = effective[i] > 0 ? effective[i] : prios[i];
        if (p > bestp) { bestp = p; best = i; }
    }
    (void)running;
    return best;
}
