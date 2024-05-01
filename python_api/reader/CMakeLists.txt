add_library(vnvreader SHARED)
add_library(VnV::Reader ALIAS vnvreader)
target_include_directories(vnvreader PUBLIC ${CMAKE_CURRENT_LIST_DIR}/include)
target_link_libraries(vnvreader PRIVATE pthread)
add_subdirectory(src)
add_subdirectory(shared)
add_shared_sources(vnvreader)


add_executable(test1   ${CMAKE_CURRENT_LIST_DIR}/main.cpp)
target_link_libraries(test1 PUBLIC vnvreader)
