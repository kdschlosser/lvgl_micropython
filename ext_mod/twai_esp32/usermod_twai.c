#include "py/runtime.h"
#include "py/obj.h"
#include "driver/twai.h"

static mp_obj_t twai_init_module(size_t n_args, const mp_obj_t *args) {
    int tx_pin = mp_obj_get_int(args[0]);
    int rx_pin = mp_obj_get_int(args[1]);
    int baudrate = mp_obj_get_int(args[2]);

    twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT(tx_pin, rx_pin, TWAI_MODE_NORMAL);
    twai_timing_config_t t_config;

    if (baudrate == 50000) {
        twai_timing_config_t t_cfg = TWAI_TIMING_CONFIG_50KBITS();
        t_config = t_cfg;
    } else if (baudrate == 250000) {
        twai_timing_config_t t_cfg = TWAI_TIMING_CONFIG_250KBITS();
        t_config = t_cfg;
    } else {
        twai_timing_config_t t_cfg = TWAI_TIMING_CONFIG_500KBITS();
        t_config = t_cfg;
    }

    twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

    if (twai_driver_install(&g_config, &t_config, &f_config) != ESP_OK) {
        mp_raise_ValueError(MP_ERROR_TEXT("Failed to install TWAI driver"));
    }
    if (twai_start() != ESP_OK) {
        mp_raise_ValueError(MP_ERROR_TEXT("Failed to start TWAI driver"));
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(twai_init_obj, 3, 3, twai_init_module);

static mp_obj_t twai_send_msg(size_t n_args, const mp_obj_t *args) {
    uint32_t id = mp_obj_get_int(args[0]);
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(args[1], &bufinfo, MP_BUFFER_READ);

    twai_message_t message = {0};
    message.identifier = id;
    message.data_length_code = bufinfo.len > 8 ? 8 : bufinfo.len;
    for (int i = 0; i < message.data_length_code; i++) {
        message.data[i] = ((uint8_t*)bufinfo.buf)[i];
    }

    if (twai_transmit(&message, pdMS_TO_TICKS(100)) != ESP_OK) {
        mp_raise_ValueError(MP_ERROR_TEXT("Failed to transmit CAN message"));
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(twai_send_obj, 2, 2, twai_send_msg);

static const mp_rom_map_elem_t twai_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_twai) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&twai_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_send), MP_ROM_PTR(&twai_send_obj) },
};
static MP_DEFINE_CONST_DICT(twai_module_globals, twai_module_globals_table);

const mp_obj_module_t twai_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&twai_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_twai, twai_user_cmodule);