add_library(usermod_twai INTERFACE)

target_sources(usermod_twai INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/usermod_twai.c
)

target_include_directories(usermod_twai INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod INTERFACE usermod_twai)