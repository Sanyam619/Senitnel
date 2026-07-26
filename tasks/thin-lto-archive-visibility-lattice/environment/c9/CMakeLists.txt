cmake_minimum_required(VERSION 3.16)
project(c9 C)

if(NOT DEFINED ARCHIVE_MEMBERS)
  set(ARCHIVE_MEMBERS 4)
endif()
if(NOT DEFINED SLOT_VIS_INCLUDE)
  set(SLOT_VIS_INCLUDE "${CMAKE_CURRENT_SOURCE_DIR}/../include")
endif()

add_library(c9_objs OBJECT src/obj_a.c src/obj_b.c)
target_include_directories(c9_objs PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
  ${SLOT_VIS_INCLUDE}
)
target_compile_definitions(c9_objs PRIVATE ARCHIVE_MEMBERS=${ARCHIVE_MEMBERS})

add_library(c9 STATIC $<TARGET_OBJECTS:c9_objs>)
