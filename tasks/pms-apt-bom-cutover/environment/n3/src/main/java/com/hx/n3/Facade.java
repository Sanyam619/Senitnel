package com.hx.n3;

import com.hx.m2.CoreType;

public final class Facade {
  public String open() {
    return new CoreType().label();
  }
}
