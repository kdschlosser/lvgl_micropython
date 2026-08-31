#pragma once

#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>

#include "py/obj.h"
#include "esp_twai_types.h"

typedef struct _twai_node_obj_t twai_node_obj_t;

#define TWAI_FRAME_DATA_LEN (8)
#define TWAI_FLAG_EXTENDED (0x01)
#define TWAI_FLAG_RTR (0x02)
#define TWAI_FLAG_MASK (TWAI_FLAG_EXTENDED | TWAI_FLAG_RTR)

typedef struct _twai_frame_obj_t {
    mp_obj_base_t base;
    mp_obj_t data;
    uint32_t id;
    uint8_t dlc;
    uint8_t flags;
    atomic_bool in_use;
    twai_node_obj_t *owner;
    twai_frame_t native_frame;
} twai_frame_obj_t;

extern const mp_obj_type_t twai_frame_type;

bool twai_frame_try_acquire(twai_frame_obj_t *frame);
void twai_frame_release_from_driver(twai_frame_obj_t *frame);
bool twai_frame_is_in_use(const twai_frame_obj_t *frame);
uint8_t *twai_frame_data_buf(twai_frame_obj_t *frame);
bool twai_frame_prepare_tx(twai_frame_obj_t *frame);
void twai_frame_finish_rx(twai_frame_obj_t *frame);
