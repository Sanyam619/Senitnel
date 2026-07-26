#include <jni.h>
#include <stdio.h>
#include <string.h>

#include "knit_xv.h"

static int read_token(const char *path, int *pack, int *mode, unsigned char *tip, int tip_cap, int *tip_len)
{
    FILE *f = fopen(path, "rb");
    unsigned char hdr[7];
    if (!f) {
        return -1;
    }
    if (fread(hdr, 1, 7, f) != 7) {
        fclose(f);
        return -1;
    }
    if (memcmp(hdr, "JPMS", 4) != 0) {
        fclose(f);
        return -1;
    }
    *pack = hdr[4];
    *mode = hdr[5];
    *tip_len = hdr[6];
    if (*tip_len < 0 || *tip_len >= tip_cap) {
        fclose(f);
        return -1;
    }
    if (fread(tip, 1, (size_t)*tip_len, f) != (size_t)*tip_len) {
        fclose(f);
        return -1;
    }
    tip[*tip_len] = 0;
    fclose(f);
    return 0;
}

JNIEXPORT jint JNICALL Java_lib_NativeBridge_nativeKnit(
    JNIEnv *env, jclass cls, jint pack, jint mode, jint wantRank, jint wantMode)
{
    struct row_x a;
    struct slot_x b;
    (void)env;
    (void)cls;
    a.pack_rank = pack;
    a.mode_tag = mode;
    a.want_rank = wantRank;
    a.want_mode = wantMode;
    memset(&b, 0, sizeof(b));
    knit_xv(&a, &b);
    if (!b.pack_ok) {
        return 0;
    }
    return 1 | ((b.mode_tag & 0xff) << 8);
}

JNIEXPORT jlong JNICALL Java_lib_NativeBridge_nativeSkim(
    JNIEnv *env, jclass cls, jbyteArray arr)
{
    jsize n;
    jbyte *bytes;
    unsigned h;
    (void)cls;
    n = (*env)->GetArrayLength(env, arr);
    bytes = (*env)->GetByteArrayElements(env, arr, 0);
    h = skim_xv((const unsigned char *)bytes, (unsigned)n);
    (*env)->ReleaseByteArrayElements(env, arr, bytes, JNI_ABORT);
    return (jlong)h;
}

JNIEXPORT jint JNICALL Java_lib_NativeBridge_nativeReadPack(
    JNIEnv *env, jclass cls, jstring jpath)
{
    const char *path;
    int pack = 0, mode = 0, tip_len = 0;
    unsigned char tip[64];
    (void)cls;
    path = (*env)->GetStringUTFChars(env, jpath, 0);
    if (read_token(path, &pack, &mode, tip, sizeof(tip), &tip_len) != 0) {
        (*env)->ReleaseStringUTFChars(env, jpath, path);
        return -1;
    }
    (*env)->ReleaseStringUTFChars(env, jpath, path);
    return (pack & 0xff) | ((mode & 0xff) << 8);
}
