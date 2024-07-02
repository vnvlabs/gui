add_library(vnvreader SHARED)
add_library(VnV::Reader ALIAS vnvreader)
target_include_directories(vnvreader PUBLIC ${CMAKE_CURRENT_LIST_DIR}/include)
add_subdirectory(src)
add_subdirectory(shared)
add_shared_sources(vnvreader)

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)
target_link_libraries(vnvreader PRIVATE Threads::Threads)

add_executable(test1   ${CMAKE_CURRENT_LIST_DIR}/main.cpp)
target_link_libraries(test1 PUBLIC vnvreader)
