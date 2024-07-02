project(vnvgui LANGUAGES CXX )
cmake_minimum_required(VERSION 3.10)
set(PROJECT_VERSION 1.0.0)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS YES)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)


# SWIG: use standard target name.
if(POLICY CMP0078)
  cmake_policy(SET CMP0078 NEW)
endif()

# SWIG: use SWIG_MODULE_NAME property.
if(POLICY CMP0086)
  cmake_policy(SET CMP0086 NEW)
endif()

# Python is required to build the reports.
find_package(
  Python3
  COMPONENTS Interpreter Development
  REQUIRED)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  message(STATUS "No build type selected, default to RelWithDebInfo")
  set(CMAKE_BUILD_TYPE RelWithDebInfo CACHE STRING "Build type (default RelWitDebInfo)")
endif()

add_subdirectory(reader)

find_package(SWIG 4 REQUIRED)
find_package(PythonLibs REQUIRED)

include(${SWIG_USE_FILE})

set_property(SOURCE IOutputReader.i PROPERTY CPLUSPLUS ON)
set_property(SOURCE IOutputReader.i PROPERTY SWIG_MODULE_NAME VnVReader)
swig_add_library(
    VnVReader
    TYPE SHARED
    LANGUAGE python
    SOURCES IOutputReader.i)

  # Add the python include directories and link the library. For some reason, we
  # don't need to link the library on linux, but we do need to link it on mac.
  # target_include_directories(VnVReader PRIVATE ../injection/include)
  target_link_libraries(VnVReader PRIVATE Python3::Python)
  target_compile_definitions(VnVReader PRIVATE -DVNV_IGNORE=0)
  set_property(TARGET VnVReader PROPERTY SWIG_USE_TARGET_INCLUDE_DIRECTORIES ON)
  target_link_libraries(VnVReader PRIVATE VnV::Reader)
  target_include_directories(VnVReader PRIVATE ${CMAKE_CURRENT_LIST_DIR}/reader/shared/include)

  file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/__init__.py DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
