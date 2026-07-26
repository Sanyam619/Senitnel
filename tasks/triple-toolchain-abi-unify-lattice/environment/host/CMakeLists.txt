cmake_minimum_required(VERSION 3.16)
project(slot_host C)

if(NOT DEFINED PACK_WIDTH)
  set(PACK_WIDTH 8)
endif()
if(NOT DEFINED SLOT_ABI_INCLUDE)
  message(FATAL_ERROR "SLOT_ABI_INCLUDE required")
endif()

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../c6 ${CMAKE_BINARY_DIR}/c6)

add_executable(slot_host main.c $<TARGET_OBJECTS:c6_objs>)
target_include_directories(slot_host PRIVATE
  ${SLOT_ABI_INCLUDE}
  ${CMAKE_SOURCE_DIR}/../c6/include
)
target_link_libraries(slot_host PRIVATE dl)
