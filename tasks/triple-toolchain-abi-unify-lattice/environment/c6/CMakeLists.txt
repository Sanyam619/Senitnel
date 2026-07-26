cmake_minimum_required(VERSION 3.16)
project(c6_objs C)

if(NOT DEFINED PACK_WIDTH)
  set(PACK_WIDTH 8)
endif()

include(${CMAKE_CURRENT_SOURCE_DIR}/xv_w.cmake)

add_library(c6_objs OBJECT src/obj_a.c src/obj_b.c)
target_include_directories(c6_objs PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
  ${SLOT_ABI_INCLUDE}
)
target_compile_definitions(c6_objs PRIVATE PACK_WIDTH=${PACK_WIDTH})
