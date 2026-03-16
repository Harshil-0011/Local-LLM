cmake_minimum_required(VERSION 3.10)
project(local_perplex_core)

set(CMAKE_CXX_STANDARD 17)

# Attempt to find pybind11 automatically. On Windows/Linux, ensure pybind11 is installed via pip.
execute_process(
    COMMAND python3 -m pybind11 --cmakedir
    OUTPUT_VARIABLE PYBIND11_CMAKEDIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
set(pybind11_DIR ${PYBIND11_CMAKEDIR})
find_package(pybind11 REQUIRED)

pybind11_add_module(local_perplex_core src/core.cpp)
