#ifndef STATE_IO_H
#define STATE_IO_H

int ensure_dir(const char *path);
int write_text(const char *path, const char *body);
int read_text(const char *path, char *buf, int bun);
int file_exists(const char *path);

#endif
