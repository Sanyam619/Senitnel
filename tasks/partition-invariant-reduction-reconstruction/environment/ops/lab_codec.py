import struct


def f64_bits(v: float) -> str:
    return format(struct.unpack(">Q", struct.pack(">d", v))[0], "016x")
