#ifndef RT_ABI_H
#define RT_ABI_H

#ifdef __cplusplus
extern "C" {
#endif

int fold_w(const unsigned char *a, int b, int c);
double score_u(unsigned int epoch, int lane, int mixed, unsigned int salt);
int decoy_fold(const unsigned char *a, int b, int c);

#ifdef __cplusplus
}
#endif

#endif
