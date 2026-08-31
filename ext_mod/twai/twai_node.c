#include "twai_node.h"

#include <inttypes.h>

#include "py/mperrno.h"
#include "py/runtime.h"
#include "freertos/FreeRTOS.h"
#include "freertos/idf_additions.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_twai_onchip.h"

#define TWAI_TX_TASK_STACK_SIZE (3072)
#define TWAI_TX_TASK_PRIORITY (tskIDLE_PRIORITY + 1)

static const char *TAG = "twai";

static void twai_raise_esp_err(esp_err_t err) {
    mp_raise_OSError(err);
}

static mp_obj_tuple_t *twai_pool_tuple(mp_obj_t pool_in, const char *name) {
    size_t len;
    mp_obj_t *items;
    mp_obj_get_array(pool_in, &len, &items);
    if (len == 0) {
        mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("%s must not be empty"), name);
    }
    for (size_t i = 0; i < len; ++i) {
        if (mp_obj_get_type(items[i]) != &twai_frame_type) {
            mp_raise_TypeError(MP_ERROR_TEXT("pool entries must be Frame objects"));
        }
        for (size_t j = 0; j < i; ++j) {
            if (items[i] == items[j]) {
                mp_raise_ValueError(MP_ERROR_TEXT("pool contains duplicate Frame"));
            }
        }
    }
    return MP_OBJ_TO_PTR(mp_obj_new_tuple(len, items));
}

static bool twai_tuple_has_frame(const mp_obj_tuple_t *pool, const twai_frame_obj_t *frame) {
    for (size_t i = 0; i < pool->len; ++i) {
        if (MP_OBJ_TO_PTR(pool->items[i]) == frame) {
            return true;
        }
    }
    return false;
}

bool twai_node_frame_is_rx_member(const twai_node_obj_t *self, const twai_frame_obj_t *frame) {
    return twai_tuple_has_frame(MP_OBJ_TO_PTR(self->rx_pool), frame);
}

static bool IRAM_ATTR twai_on_rx_done(twai_node_handle_t handle, const twai_rx_done_event_data_t *edata, void *user_ctx) {
    (void)edata;
    twai_node_obj_t *self = user_ctx;
    twai_frame_obj_t *frame = NULL;
    BaseType_t task_woken = pdFALSE;

    // The node driver has already read and released the hardware FIFO before
    // invoking this callback.  receive_from_isr only copies its internal frame.
    if (xQueueReceiveFromISR(self->rx_free_queue, &frame, &task_woken) != pdTRUE) {
        atomic_fetch_add(&self->dropped_rx_count, 1);
        return task_woken == pdTRUE;
    }

    uint8_t *data_buf = twai_frame_data_buf(frame);
    if (data_buf == NULL) {
        atomic_fetch_add(&self->dropped_rx_count, 1);
        xQueueSendFromISR(self->rx_free_queue, &frame, &task_woken);
        return task_woken == pdTRUE;
    }
    frame->native_frame.buffer = data_buf;
    frame->native_frame.buffer_len = TWAI_FRAME_DATA_LEN;
    if (twai_node_receive_from_isr(handle, &frame->native_frame) != ESP_OK) {
        atomic_fetch_add(&self->dropped_rx_count, 1);
        xQueueSendFromISR(self->rx_free_queue, &frame, &task_woken);
        return task_woken == pdTRUE;
    }

    twai_frame_finish_rx(frame);
    atomic_store(&frame->in_use, true);
    if (xQueueSendFromISR(self->rx_ready_queue, &frame, &task_woken) != pdTRUE) {
        atomic_store(&frame->in_use, false);
        atomic_fetch_add(&self->dropped_rx_count, 1);
        xQueueSendFromISR(self->rx_free_queue, &frame, &task_woken);
    }
    return task_woken == pdTRUE;
}

static bool IRAM_ATTR twai_on_tx_done(twai_node_handle_t handle, const twai_tx_done_event_data_t *edata, void *user_ctx) {
    (void)handle;
    twai_node_obj_t *self = user_ctx;
    mp_obj_tuple_t *pool = MP_OBJ_TO_PTR(self->tx_pool);
    for (size_t i = 0; i < pool->len; ++i) {
        twai_frame_obj_t *frame = MP_OBJ_TO_PTR(pool->items[i]);
        if (&frame->native_frame == edata->done_tx_frame) {
            twai_frame_release_from_driver(frame);
            break;
        }
    }
    return false;
}

static bool IRAM_ATTR twai_on_error(twai_node_handle_t handle, const twai_error_event_data_t *edata, void *user_ctx) {
    (void)handle;
    (void)edata;
    twai_node_obj_t *self = user_ctx;
    atomic_fetch_add(&self->error_count, 1);
    return false;
}

static bool IRAM_ATTR twai_on_state_change(twai_node_handle_t handle, const twai_state_change_event_data_t *edata, void *user_ctx) {
    (void)handle;
    twai_node_obj_t *self = user_ctx;
    if (edata->new_sta == TWAI_ERROR_BUS_OFF) {
        atomic_fetch_add(&self->bus_off_count, 1);
    }
    return false;
}

static void twai_tx_task(void *arg) {
    twai_node_obj_t *self = arg;
    for (;;) {
        twai_frame_obj_t *frame = NULL;
        if (xQueueReceive(self->tx_request_queue, &frame, portMAX_DELAY) != pdTRUE) {
            continue;
        }
        if (frame == NULL) {
            break;
        }
        if (!twai_frame_prepare_tx(frame) || twai_node_transmit(self->node, &frame->native_frame, 0) != ESP_OK) {
            twai_frame_release_from_driver(frame);
        }
    }
    self->tx_task = NULL;
    vTaskDelete(NULL);
}

static void twai_stop_tx_task(twai_node_obj_t *self) {
    if (self->tx_task == NULL) {
        return;
    }
    twai_frame_obj_t *stop = NULL;
    xQueueSend(self->tx_request_queue, &stop, portMAX_DELAY);
    while (self->tx_task != NULL) {
        vTaskDelay(1);
    }
}

static bool twai_all_frames_idle(const mp_obj_tuple_t *pool) {
    for (size_t i = 0; i < pool->len; ++i) {
        if (twai_frame_is_in_use(MP_OBJ_TO_PTR(pool->items[i]))) {
            return false;
        }
    }
    return true;
}

static void twai_log_counters(const twai_node_obj_t *self) {
    uint_fast32_t error_count = atomic_load(&self->error_count);
    uint_fast32_t bus_off_count = atomic_load(&self->bus_off_count);
    uint_fast32_t dropped_rx_count = atomic_load(&self->dropped_rx_count);
    if (error_count || bus_off_count || dropped_rx_count) {
        ESP_LOGI(TAG, "TWAI counters: error=%" PRIuFAST32 " bus_off=%" PRIuFAST32 " dropped_rx=%" PRIuFAST32,
            error_count, bus_off_count, dropped_rx_count);
    }
}

static mp_obj_t twai_node_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *all_args) {
    enum { ARG_tx, ARG_rx, ARG_bitrate, ARG_rx_pool, ARG_tx_pool };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_tx, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_rx, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_bitrate, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_rx_pool, MP_ARG_REQUIRED | MP_ARG_KW_ONLY | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_tx_pool, MP_ARG_REQUIRED | MP_ARG_KW_ONLY | MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all_kw_array(n_args, n_kw, all_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);
    if (args[ARG_bitrate].u_int <= 0) {
        mp_raise_ValueError(MP_ERROR_TEXT("bitrate must be positive"));
    }

    mp_obj_tuple_t *rx_pool = twai_pool_tuple(args[ARG_rx_pool].u_obj, "rx_pool");
    mp_obj_tuple_t *tx_pool = twai_pool_tuple(args[ARG_tx_pool].u_obj, "tx_pool");
    for (size_t i = 0; i < rx_pool->len; ++i) {
        if (twai_tuple_has_frame(tx_pool, MP_OBJ_TO_PTR(rx_pool->items[i]))) {
            mp_raise_ValueError(MP_ERROR_TEXT("a Frame cannot be in both pools"));
        }
    }

    twai_node_obj_t *self = mp_obj_malloc(twai_node_obj_t, type);
    self->node = NULL;
    self->rx_free_queue = xQueueCreate(rx_pool->len, sizeof(twai_frame_obj_t *));
    self->rx_ready_queue = xQueueCreate(rx_pool->len, sizeof(twai_frame_obj_t *));
    self->tx_request_queue = xQueueCreate(tx_pool->len, sizeof(twai_frame_obj_t *));
    if (self->rx_free_queue == NULL || self->rx_ready_queue == NULL || self->tx_request_queue == NULL) {
        mp_raise_msg(&mp_type_MemoryError, MP_ERROR_TEXT("unable to create TWAI queues"));
    }

    self->rx_pool = MP_OBJ_FROM_PTR(rx_pool);
    self->tx_pool = MP_OBJ_FROM_PTR(tx_pool);
    self->rx_pool_len = rx_pool->len;
    self->tx_pool_len = tx_pool->len;
    self->tx_task = NULL;
    self->started = false;
    atomic_init(&self->error_count, 0);
    atomic_init(&self->bus_off_count, 0);
    atomic_init(&self->dropped_rx_count, 0);

    for (size_t i = 0; i < rx_pool->len; ++i) {
        twai_frame_obj_t *frame = MP_OBJ_TO_PTR(rx_pool->items[i]);
        if (frame->owner != NULL || twai_frame_is_in_use(frame)) {
            mp_raise_ValueError(MP_ERROR_TEXT("Frame already belongs to a Node"));
        }
        xQueueSend(self->rx_free_queue, &frame, 0);
    }
    for (size_t i = 0; i < tx_pool->len; ++i) {
        twai_frame_obj_t *frame = MP_OBJ_TO_PTR(tx_pool->items[i]);
        if (frame->owner != NULL || twai_frame_is_in_use(frame)) {
            mp_raise_ValueError(MP_ERROR_TEXT("Frame already belongs to a Node"));
        }
    }

    twai_onchip_node_config_t config = {
        .io_cfg = {
            .tx = (gpio_num_t)args[ARG_tx].u_int,
            .rx = (gpio_num_t)args[ARG_rx].u_int,
            .quanta_clk_out = GPIO_NUM_NC,
            .bus_off_indicator = GPIO_NUM_NC,
        },
        .bit_timing = {.bitrate = (uint32_t)args[ARG_bitrate].u_int},
        .data_timing = {},
        .fail_retry_cnt = 3,
        .tx_queue_depth = tx_pool->len,
        .intr_priority = 0,
        .flags = {},
    };
    esp_err_t err = twai_new_node_onchip(&config, &self->node);
    if (err != ESP_OK) {
        twai_raise_esp_err(err);
    }
    twai_event_callbacks_t callbacks = {
        .on_tx_done = twai_on_tx_done,
        .on_rx_done = twai_on_rx_done,
        .on_state_change = twai_on_state_change,
        .on_error = twai_on_error,
    };
    err = twai_node_register_event_callbacks(self->node, &callbacks, self);
    if (err != ESP_OK) {
        twai_node_delete(self->node);
        self->node = NULL;
        twai_raise_esp_err(err);
    }
    for (size_t i = 0; i < rx_pool->len; ++i) {
        ((twai_frame_obj_t *)MP_OBJ_TO_PTR(rx_pool->items[i]))->owner = self;
    }
    for (size_t i = 0; i < tx_pool->len; ++i) {
        ((twai_frame_obj_t *)MP_OBJ_TO_PTR(tx_pool->items[i]))->owner = self;
    }
    return MP_OBJ_FROM_PTR(self);
}

static mp_obj_t twai_node_start(mp_obj_t self_in) {
    twai_node_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (self->started) {
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("TWAI node already started"));
    }
    if (xTaskCreatePinnedToCore(twai_tx_task, "twai_tx", TWAI_TX_TASK_STACK_SIZE, self,
        TWAI_TX_TASK_PRIORITY, (TaskHandle_t *)&self->tx_task, 0) != pdPASS) {
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("failed to create TWAI task"));
    }
    esp_err_t err = twai_node_enable(self->node);
    if (err != ESP_OK) {
        twai_stop_tx_task(self);
        twai_raise_esp_err(err);
    }
    self->started = true;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(twai_node_start_obj, twai_node_start);

static mp_obj_t twai_node_send(mp_obj_t self_in, mp_obj_t frame_in) {
    twai_node_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (!self->started) {
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("TWAI node is not started"));
    }
    if (mp_obj_get_type(frame_in) != &twai_frame_type) {
        mp_raise_TypeError(MP_ERROR_TEXT("send expects a Frame"));
    }
    twai_frame_obj_t *frame = MP_OBJ_TO_PTR(frame_in);
    if (!twai_tuple_has_frame(MP_OBJ_TO_PTR(self->tx_pool), frame)) {
        mp_raise_ValueError(MP_ERROR_TEXT("Frame is not in this Node's tx_pool"));
    }
    if (twai_frame_data_buf(frame) == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("Frame data must remain 8 bytes"));
    }
    if (!twai_frame_try_acquire(frame)) {
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("frame is in use"));
    }
    if (xQueueSend(self->tx_request_queue, &frame, 0) != pdTRUE) {
        twai_frame_release_from_driver(frame);
        mp_raise_OSError(MP_EAGAIN);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(twai_node_send_obj, twai_node_send);

static mp_obj_t twai_node_recv(mp_obj_t self_in) {
    twai_node_obj_t *self = MP_OBJ_TO_PTR(self_in);
    twai_frame_obj_t *frame = NULL;
    if (xQueueReceive(self->rx_ready_queue, &frame, 0) != pdTRUE) {
        return mp_const_none;
    }
    return MP_OBJ_FROM_PTR(frame);
}
static MP_DEFINE_CONST_FUN_OBJ_1(twai_node_recv_obj, twai_node_recv);

static mp_obj_t twai_node_pending(mp_obj_t self_in) {
    twai_node_obj_t *self = MP_OBJ_TO_PTR(self_in);
    return mp_obj_new_int_from_uint(uxQueueMessagesWaiting(self->rx_ready_queue));
}
static MP_DEFINE_CONST_FUN_OBJ_1(twai_node_pending_obj, twai_node_pending);

static mp_obj_t twai_node_deinit(mp_obj_t self_in) {
    twai_node_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (self->node == NULL) {
        return mp_const_none;
    }
    if (!twai_all_frames_idle(MP_OBJ_TO_PTR(self->rx_pool)) || !twai_all_frames_idle(MP_OBJ_TO_PTR(self->tx_pool))
        || uxQueueMessagesWaiting(self->rx_ready_queue) != 0 || uxQueueMessagesWaiting(self->tx_request_queue) != 0) {
        mp_raise_OSError(MP_EBUSY);
    }
    twai_stop_tx_task(self);
    if (self->started) {
        esp_err_t err = twai_node_disable(self->node);
        if (err != ESP_OK) {
            twai_raise_esp_err(err);
        }
        self->started = false;
    }
    twai_event_callbacks_t callbacks = {};
    twai_node_register_event_callbacks(self->node, &callbacks, NULL);
    twai_log_counters(self);
    esp_err_t err = twai_node_delete(self->node);
    if (err != ESP_OK) {
        twai_raise_esp_err(err);
    }
    self->node = NULL;
    mp_obj_tuple_t *rx_pool = MP_OBJ_TO_PTR(self->rx_pool);
    mp_obj_tuple_t *tx_pool = MP_OBJ_TO_PTR(self->tx_pool);
    for (size_t i = 0; i < self->rx_pool_len; ++i) {
        ((twai_frame_obj_t *)MP_OBJ_TO_PTR(rx_pool->items[i]))->owner = NULL;
    }
    for (size_t i = 0; i < self->tx_pool_len; ++i) {
        ((twai_frame_obj_t *)MP_OBJ_TO_PTR(tx_pool->items[i]))->owner = NULL;
    }
    vQueueDelete(self->rx_free_queue);
    vQueueDelete(self->rx_ready_queue);
    vQueueDelete(self->tx_request_queue);
    self->rx_free_queue = NULL;
    self->rx_ready_queue = NULL;
    self->tx_request_queue = NULL;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(twai_node_deinit_obj, twai_node_deinit);

void twai_node_release_rx_frame(twai_frame_obj_t *frame) {
    twai_node_obj_t *self = frame->owner;
    if (self == NULL || !twai_node_frame_is_rx_member(self, frame)) {
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("Frame is not an RX frame"));
    }
    if (!twai_frame_is_in_use(frame)) {
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("Frame is not pending"));
    }
    // Clear in_use before publishing to the ISR.  Publishing first would let
    // an RX interrupt reuse the Frame and then have this function clear the
    // new frame's in_use flag.
    twai_frame_release_from_driver(frame);
    if (xQueueSend(self->rx_free_queue, &frame, 0) != pdTRUE) {
        atomic_store(&frame->in_use, true);
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("RX free pool is full"));
    }
}

static const mp_rom_map_elem_t twai_node_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_start), MP_ROM_PTR(&twai_node_start_obj) },
    { MP_ROM_QSTR(MP_QSTR_send), MP_ROM_PTR(&twai_node_send_obj) },
    { MP_ROM_QSTR(MP_QSTR_recv), MP_ROM_PTR(&twai_node_recv_obj) },
    { MP_ROM_QSTR(MP_QSTR_pending), MP_ROM_PTR(&twai_node_pending_obj) },
    { MP_ROM_QSTR(MP_QSTR_deinit), MP_ROM_PTR(&twai_node_deinit_obj) },
};
static MP_DEFINE_CONST_DICT(twai_node_locals_dict, twai_node_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    twai_node_type,
    MP_QSTR_Node,
    MP_TYPE_FLAG_NONE,
    make_new, twai_node_make_new,
    locals_dict, &twai_node_locals_dict
    );
