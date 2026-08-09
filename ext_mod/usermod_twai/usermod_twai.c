#include "py/runtime.h"
#include "py/obj.h"
#include "driver/twai.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

// -------------------------------------------------------------------
// ۱. تابع init
// -------------------------------------------------------------------
static mp_obj_t twai_init_func(size_t n_args, const mp_obj_t *args) {
    int tx_pin = mp_obj_get_int(args[0]);
    int rx_pin = mp_obj_get_int(args[1]);
    int baudrate = mp_obj_get_int(args[2]);

    twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT((gpio_num_t)tx_pin, (gpio_num_t)rx_pin, TWAI_MODE_NORMAL);
    twai_timing_config_t t_config;

    if (baudrate == 50000) {
        twai_timing_config_t t_tmp = TWAI_TIMING_CONFIG_50KBITS();
        t_config = t_tmp;
    } else if (baudrate == 100000) {
        twai_timing_config_t t_tmp = TWAI_TIMING_CONFIG_100KBITS();
        t_config = t_tmp;
    } else if (baudrate == 250000) {
        twai_timing_config_t t_tmp = TWAI_TIMING_CONFIG_250KBITS();
        t_config = t_tmp;
    } else if (baudrate == 500000) {
        twai_timing_config_t t_tmp = TWAI_TIMING_CONFIG_500KBITS();
        t_config = t_tmp;
    } else {
        mp_raise_ValueError(MP_ERROR_TEXT("Unsupported baudrate"));
    }

    twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

    if (twai_driver_install(&g_config, &t_config, &f_config) != ESP_OK) {
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("Failed to install TWAI driver"));
    }

    if (twai_start() != ESP_OK) {
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("Failed to start TWAI driver"));
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(twai_init_obj, 3, 3, twai_init_func);

// -------------------------------------------------------------------
// ۲. تابع send
// -------------------------------------------------------------------
static mp_obj_t twai_send_func(mp_obj_t id_obj, mp_obj_t data_obj) {
    uint32_t id = mp_obj_get_int(id_obj);
    
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(data_obj, &bufinfo, MP_BUFFER_READ);

    if (bufinfo.len > 8) {
        mp_raise_ValueError(MP_ERROR_TEXT("CAN data frame cannot exceed 8 bytes"));
    }

    twai_message_t tx_msg = {0};
    tx_msg.identifier = id;
    tx_msg.data_length_code = bufinfo.len;
    for (size_t i = 0; i < bufinfo.len; i++) {
        tx_msg.data[i] = ((uint8_t *)bufinfo.buf)[i];
    }

    if (twai_transmit(&tx_msg, pdMS_TO_TICKS(1000)) != ESP_OK) {
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("Failed to transmit CAN message"));
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(twai_send_obj, twai_send_func);

// -------------------------------------------------------------------
// ۳. تابع receive (تغییر نام تابع به twai_receive_func جهت جلوگیری از تداخل)
// -------------------------------------------------------------------
static mp_obj_t twai_receive_func(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_timeout };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_timeout, MP_ARG_INT, {.u_int = 10} },
    };

    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    uint32_t timeout_ms = args[ARG_timeout].u_int;

    twai_message_t rx_msg;
    esp_err_t res = twai_receive(&rx_msg, pdMS_TO_TICKS(timeout_ms));

    if (res == ESP_OK) {
        mp_obj_t data_bytes = mp_obj_new_bytes(rx_msg.data, rx_msg.data_length_code);
        
        mp_obj_t tuple[4];
        tuple[0] = mp_obj_new_int(rx_msg.identifier);
        tuple[1] = data_bytes;
        tuple[2] = mp_obj_new_bool(rx_msg.extd);
        tuple[3] = mp_obj_new_bool(rx_msg.rtr);

        return mp_obj_new_tuple(4, tuple);
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(twai_receive_obj, 0, twai_receive_func);

// -------------------------------------------------------------------
// ۴. جدول ماژول و ثبت در MicroPython
// -------------------------------------------------------------------
static const mp_rom_map_elem_t twai_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_twai) },
    { MP_ROM_QSTR(MP_QSTR_init),     MP_ROM_PTR(&twai_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_send),     MP_ROM_PTR(&twai_send_obj) },
    { MP_ROM_QSTR(MP_QSTR_recv),     MP_ROM_PTR(&twai_receive_obj) },
    { MP_ROM_QSTR(MP_QSTR_receive),  MP_ROM_PTR(&twai_receive_obj) },
};
static MP_DEFINE_CONST_DICT(twai_module_globals, twai_module_globals_table);

const mp_obj_module_t twai_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&twai_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_twai, twai_user_cmodule);