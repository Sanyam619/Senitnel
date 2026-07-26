#include <jni.h>

JNIEXPORT jint JNICALL
Java_io_helix_bridge_NativeHook_ping(JNIEnv *env, jclass cls, jint x)
{
    (void)env;
    (void)cls;
    return x + 1;
}
