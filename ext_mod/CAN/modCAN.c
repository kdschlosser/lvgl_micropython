#include "py/obj.h"
#include "py/runtime.h"

#include "CAN_frame.h"
#include "CAN_node.h"

static const mp_rom_map_elem_t CAN_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_CAN) },
    { MP_ROM_QSTR(MP_QSTR_Frame), MP_ROM_PTR(&twai_frame_type) },
    { MP_ROM_QSTR(MP_QSTR_Node), MP_ROM_PTR(&twai_node_type) },
    { MP_ROM_QSTR(MP_QSTR_EXTENDED), MP_ROM_INT(TWAI_FLAG_EXTENDED) },
    { MP_ROM_QSTR(MP_QSTR_RTR), MP_ROM_INT(TWAI_FLAG_RTR) },
};
static MP_DEFINE_CONST_DICT(CAN_module_globals, CAN_module_globals_table);

const mp_obj_module_t mp_module_CAN = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&CAN_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_CAN, mp_module_CAN);
