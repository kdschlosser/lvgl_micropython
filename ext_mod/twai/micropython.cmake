# TWAI user module for the ESP-IDF node-based driver.

add_library(usermod_twai INTERFACE)

# The ESP32 port builds its main component after loading user modules, so this
# makes the node-based driver a direct dependency of MicroPython.
list(APPEND IDF_COMPONENTS esp_driver_twai)

target_sources(usermod_twai INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/modtwai.c
    ${CMAKE_CURRENT_LIST_DIR}/twai_frame.c
    ${CMAKE_CURRENT_LIST_DIR}/twai_node.c
)

target_include_directories(usermod_twai INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod INTERFACE usermod_twai)
