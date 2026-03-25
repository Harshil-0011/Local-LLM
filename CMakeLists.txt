cmake_minimum_required(VERSION 3.10)
project(local_perplex_core)

set(CMAKE_CXX_STANDARD 17)

if(MSVC)
    add_compile_options(/O2 /Oi /Ot /GL)
    add_link_options(/LTCG)
else()
    add_compile_options(-O3 -march=native -flto)
    add_link_options(-flto)
endif()

# Attempt to find pybind11 automatically. On Windows/Linux, ensure pybind11 is installed via pip.
execute_process(
    COMMAND python -m pybind11 --cmakedir
    OUTPUT_VARIABLE PYBIND11_CMAKEDIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
)
if(NOT PYBIND11_CMAKEDIR)
    execute_process(
        COMMAND python3 -m pybind11 --cmakedir
        OUTPUT_VARIABLE PYBIND11_CMAKEDIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
endif()
set(pybind11_DIR ${PYBIND11_CMAKEDIR})
find_package(pybind11 REQUIRED)

pybind11_add_module(local_perplex_core src/core.cpp)

# Ensure the module is placed in the local_perplex package directory
set_target_properties(local_perplex_core PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/local_perplex)
