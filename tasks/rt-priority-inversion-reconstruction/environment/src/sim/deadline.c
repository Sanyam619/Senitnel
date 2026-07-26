#include <stdint.h>

int klb_deadline_met(int64_t finish, int64_t deadline) {
    return finish <= deadline ? 1 : 0;
}
