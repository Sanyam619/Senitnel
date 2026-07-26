#include <stdio.h>
#include <stdlib.h>

void hdr_n3(int a, int b, int w, const char *path);

int main(int argc, char **argv) {
    if (argc < 5) {
        fprintf(stderr, "usage: hdrgen <fx> <fy> <w> <out.h>\n");
        return 2;
    }
    hdr_n3(atoi(argv[1]), atoi(argv[2]), atoi(argv[3]), argv[4]);
    return 0;
}
