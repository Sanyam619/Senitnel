cmake_minimum_required(VERSION 3.16)
project(lattice_host C)

if(NOT DEFINED ARCHIVE_MEMBERS)
  set(ARCHIVE_MEMBERS 4)
endif()
if(NOT DEFINED SLOT_VIS_INCLUDE)
  message(FATAL_ERROR "SLOT_VIS_INCLUDE required")
endif()

add_executable(lattice_host main.c
  ${CMAKE_CURRENT_SOURCE_DIR}/../c9/src/obj_a.c
  ${CMAKE_CURRENT_SOURCE_DIR}/../c9/src/obj_b.c
)
target_include_directories(lattice_host PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/../c9/include
  ${SLOT_VIS_INCLUDE}
)
target_compile_definitions(lattice_host PRIVATE ARCHIVE_MEMBERS=${ARCHIVE_MEMBERS})
target_link_libraries(lattice_host PRIVATE dl)
