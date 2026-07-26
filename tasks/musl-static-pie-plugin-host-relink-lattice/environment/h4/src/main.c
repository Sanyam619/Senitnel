#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "slot_api.h"

#ifndef XV_TLS_STR
#define XV_TLS_STR "unknown"
#endif

int load_slot(const char *path, int *abi_out, int *frame_out);

int main(int argc, char **argv) {
    const char *plugin = NULL;
    int i;
    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--plugin") == 0 && i + 1 < argc) {
            plugin = argv[++i];
        }
    }
    if (plugin == NULL) {
        fprintf(stderr, "usage: gateway_host --plugin <path>\n");
        return 2;
    }

    int abi = 0;
    int frame = 0;
    int rc = load_slot(plugin, &abi, &frame);
    if (rc != 0) {
        printf("{\"status\":\"fail\",\"tls_model\":\"%s\",\"plugin_abi\":\"\",\"error\":\"load_failed:%d\"}\n",
               XV_TLS_STR, rc);
        return 1;
    }

    const char *tag = (abi == 2) ? "v2" : "v1";
    /* Reject incompatible TLS models for plugin lanes. */
    if (strcmp(XV_TLS_STR, "global-dynamic") != 0) {
        printf("{\"status\":\"fail\",\"tls_model\":\"%s\",\"plugin_abi\":\"%s\",\"error\":\"tls_init\"}\n",
               XV_TLS_STR, tag);
        return 1;
    }

    if (abi == 2 && frame != 16) {
        printf("{\"status\":\"fail\",\"tls_model\":\"%s\",\"plugin_abi\":\"%s\",\"error\":\"frame_abi_mismatch\"}\n",
               XV_TLS_STR, tag);
        return 1;
    }
    if (abi == 1 && frame != 12) {
        printf("{\"status\":\"fail\",\"tls_model\":\"%s\",\"plugin_abi\":\"%s\",\"error\":\"frame_abi_mismatch\"}\n",
               XV_TLS_STR, tag);
        return 1;
    }

    printf("{\"status\":\"ok\",\"tls_model\":\"%s\",\"plugin_abi\":\"%s\",\"frame_bytes\":%d}\n",
           XV_TLS_STR, tag, frame);
    return 0;
}
