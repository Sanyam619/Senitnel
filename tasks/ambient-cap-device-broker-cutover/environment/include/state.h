#ifndef STATE_H
#define STATE_H

int ensure_dir(const char *path);
int write_text(const char *path, const char *body);
int read_text(const char *path, char *buf, int bun);
int file_exists(const char *path);
int join3(char *out, int n, const char *a, const char *b, const char *c);

#endif
