# TWAI user module for the ESP-IDF node-based driver.

add_library(usermod_CAN INTERFACE)

# The ESP32 port builds its main component after loading user modules, so this
# makes the node-based driver a direct dependency of MicroPython.
list(APPEND IDF_COMPONENTS esp_driver_twai)

target_sources(usermod_CAN INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/modCAN.c
    ${CMAKE_CURRENT_LIST_DIR}/CAN_frame.c
    ${CMAKE_CURRENT_LIST_DIR}/CAN_node.c
)

target_include_directories(usermod_CAN INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod INTERFACE usermod_CAN)
