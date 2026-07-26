#include <stdio.h>
#include <stdlib.h>

void emit_q3(int a, int b, int e, int m, const char *path);

int main(int argc, char **argv) {
    int a, b, e, m;
    if (argc < 6) {
        fprintf(stderr, "usage: visgen <a> <b> <epoch> <members> <path>\n");
        return 2;
    }
    a = atoi(argv[1]);
    b = atoi(argv[2]);
    e = atoi(argv[3]);
    m = atoi(argv[4]);
    emit_q3(a, b, e, m, argv[5]);
    return 0;
}
