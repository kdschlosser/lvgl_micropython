#include "twai_frame.h"

#include "py/objarray.h"
#include "py/runtime.h"

#include "twai_node.h"

static void twai_frame_validate_id(uint32_t id, uint8_t flags) {
    const uint32_t max_id = (flags & TWAI_FLAG_EXTENDED) ? 0x1fffffffU : 0x7ffU;
    if (id > max_id) {
        mp_raise_ValueError(MP_ERROR_TEXT("CAN id out of range"));
    }
}

static uint32_t twai_frame_get_id(mp_obj_t value) {
    mp_int_t id = mp_obj_get_int(value);
    if (id < 0) {
        mp_raise_ValueError(MP_ERROR_TEXT("CAN id out of range"));
    }
    return (uint32_t)id;
}

static uint8_t twai_frame_get_dlc(mp_obj_t value) {
    mp_int_t dlc = mp_obj_get_int(value);
    if (dlc < 0 || dlc > TWAI_FRAME_DATA_LEN) {
        mp_raise_ValueError(MP_ERROR_TEXT("DLC must be from 0 to 8"));
    }
    return (uint8_t)dlc;
}

static uint8_t twai_frame_get_flags(mp_obj_t value) {
    mp_int_t flags = mp_obj_get_int(value);
    if (flags < 0 || (flags & ~TWAI_FLAG_MASK)) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid CAN flags"));
    }
    return (uint8_t)flags;
}

static void twai_frame_check_editable(const twai_frame_obj_t *self) {
    if (twai_frame_is_in_use(self)) {
        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("frame is in use"));
    }
}

static mp_obj_t twai_frame_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *all_args) {
    enum { ARG_id, ARG_dlc, ARG_flags };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_id, MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_dlc, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 0} },
        { MP_QSTR_flags, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 0} },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all_kw_array(n_args, n_kw, all_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    // mp_obj_new_bytearray() copies its input with memcpy(), so it must not
    // receive NULL.  Allocate the bytearray before the Frame so the Frame is
    // not an unrooted GC allocation while another MicroPython allocation runs.
    static const uint8_t initial_data[TWAI_FRAME_DATA_LEN] = {0};
    mp_obj_t data = mp_obj_new_bytearray(TWAI_FRAME_DATA_LEN, initial_data);
    twai_frame_obj_t *self = mp_obj_malloc(twai_frame_obj_t, type);
    self->id = twai_frame_get_id(MP_OBJ_NEW_SMALL_INT(args[ARG_id].u_int));
    self->dlc = twai_frame_get_dlc(MP_OBJ_NEW_SMALL_INT(args[ARG_dlc].u_int));
    self->flags = twai_frame_get_flags(MP_OBJ_NEW_SMALL_INT(args[ARG_flags].u_int));
    twai_frame_validate_id(self->id, self->flags);
    self->data = data;
    atomic_init(&self->in_use, false);
    self->owner = NULL;
    twai_frame_prepare_tx(self);
    return MP_OBJ_FROM_PTR(self);
}

static void twai_frame_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {
    (void)kind;
    twai_frame_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_printf(print, "Frame(id=0x%lx, dlc=%u, flags=0x%x)", (unsigned long)self->id, self->dlc, self->flags);
}

static mp_int_t twai_frame_get_buffer(mp_obj_t self_in, mp_buffer_info_t *bufinfo, mp_uint_t flags) {
    twai_frame_obj_t *self = MP_OBJ_TO_PTR(self_in);
    (void)flags;
    uint8_t *data_buf = twai_frame_data_buf(self);
    if (data_buf == NULL) {
        mp_raise_ValueError(MP_ERROR_TEXT("Frame data must remain 8 bytes"));
    }
    bufinfo->buf = data_buf;
    bufinfo->len = TWAI_FRAME_DATA_LEN;
    bufinfo->typecode = 'B';
    return 0;
}

static mp_obj_t twai_frame_subscr(mp_obj_t self_in, mp_obj_t index, mp_obj_t value) {
    twai_frame_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (value != MP_OBJ_SENTINEL) {
        twai_frame_check_editable(self);
    }
    return mp_obj_subscr(self->data, index, value);
}

static void twai_frame_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {
    twai_frame_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (dest[0] == MP_OBJ_NULL) {
        if (attr == MP_QSTR_id) {
            dest[0] = mp_obj_new_int_from_uint(self->id);
        } else if (attr == MP_QSTR_dlc) {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->dlc);
        } else if (attr == MP_QSTR_flags) {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->flags);
        } else if (attr == MP_QSTR_data) {
            dest[0] = self->data;
        } else if (attr == MP_QSTR_in_use) {
            dest[0] = mp_obj_new_bool(twai_frame_is_in_use(self));
        } else {
            dest[1] = MP_OBJ_SENTINEL;
        }
        return;
    }

    if (dest[1] == MP_OBJ_NULL) {
        return;
    }
    twai_frame_check_editable(self);
    if (attr == MP_QSTR_id) {
        uint32_t id = twai_frame_get_id(dest[1]);
        twai_frame_validate_id(id, self->flags);
        self->id = id;
    } else if (attr == MP_QSTR_dlc) {
        self->dlc = twai_frame_get_dlc(dest[1]);
    } else if (attr == MP_QSTR_flags) {
        uint8_t flags = twai_frame_get_flags(dest[1]);
        twai_frame_validate_id(self->id, flags);
        self->flags = flags;
    } else {
        // data and in_use are deliberately read-only attributes.
        dest[1] = MP_OBJ_SENTINEL;
        return;
    }
    twai_frame_prepare_tx(self);
    dest[0] = MP_OBJ_NULL;
}

static mp_obj_t twai_frame_release(mp_obj_t self_in) {
    twai_frame_obj_t *self = MP_OBJ_TO_PTR(self_in);
    twai_node_release_rx_frame(self);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(twai_frame_release_obj, twai_frame_release);

static const mp_rom_map_elem_t twai_frame_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_release), MP_ROM_PTR(&twai_frame_release_obj) },
};
static MP_DEFINE_CONST_DICT(twai_frame_locals_dict, twai_frame_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    twai_frame_type,
    MP_QSTR_Frame,
    MP_TYPE_FLAG_NONE,
    make_new, twai_frame_make_new,
    print, twai_frame_print,
    buffer, twai_frame_get_buffer,
    subscr, twai_frame_subscr,
    attr, twai_frame_attr,
    locals_dict, &twai_frame_locals_dict
    );

bool twai_frame_try_acquire(twai_frame_obj_t *frame) {
    bool expected = false;
    return atomic_compare_exchange_strong(&frame->in_use, &expected, true);
}

void twai_frame_release_from_driver(twai_frame_obj_t *frame) {
    atomic_store(&frame->in_use, false);
}

bool twai_frame_is_in_use(const twai_frame_obj_t *frame) {
    return atomic_load(&frame->in_use);
}

uint8_t *twai_frame_data_buf(twai_frame_obj_t *frame) {
    mp_obj_array_t *data = MP_OBJ_TO_PTR(frame->data);
    return data->len == TWAI_FRAME_DATA_LEN ? data->items : NULL;
}

bool twai_frame_prepare_tx(twai_frame_obj_t *frame) {
    uint8_t *data_buf = twai_frame_data_buf(frame);
    if (data_buf == NULL) {
        return false;
    }
    frame->native_frame.header.id = frame->id;
    frame->native_frame.header.dlc = frame->dlc;
    frame->native_frame.header.ide = (frame->flags & TWAI_FLAG_EXTENDED) != 0;
    frame->native_frame.header.rtr = (frame->flags & TWAI_FLAG_RTR) != 0;
    frame->native_frame.header.fdf = false;
    frame->native_frame.header.brs = false;
    frame->native_frame.header.esi = false;
    frame->native_frame.buffer = data_buf;
    frame->native_frame.buffer_len = frame->dlc;
    return true;
}

void twai_frame_finish_rx(twai_frame_obj_t *frame) {
    frame->id = frame->native_frame.header.id;
    frame->dlc = frame->native_frame.header.dlc;
    frame->flags = (frame->native_frame.header.ide ? TWAI_FLAG_EXTENDED : 0)
        | (frame->native_frame.header.rtr ? TWAI_FLAG_RTR : 0);
}
