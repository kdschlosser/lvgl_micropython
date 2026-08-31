#pragma once

#include <stdatomic.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "py/obj.h"
#include "esp_twai.h"
#include "freertos/queue.h"
#include "freertos/task.h"

#include "CAN_frame.h"

typedef struct _twai_node_obj_t {
    mp_obj_base_t base;
    twai_node_handle_t node;
    QueueHandle_t rx_free_queue;
    QueueHandle_t rx_ready_queue;
    QueueHandle_t tx_request_queue;
    volatile TaskHandle_t tx_task;
    mp_obj_t rx_pool;
    mp_obj_t tx_pool;
    size_t rx_pool_len;
    size_t tx_pool_len;
    atomic_uint_fast32_t error_count;
    atomic_uint_fast32_t bus_off_count;
    atomic_uint_fast32_t dropped_rx_count;
    bool started;
} twai_node_obj_t;

extern const mp_obj_type_t twai_node_type;

bool twai_node_frame_is_rx_member(const twai_node_obj_t *self, const twai_frame_obj_t *frame);
void twai_node_release_rx_frame(twai_frame_obj_t *frame);
