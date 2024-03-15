
################################################################################
# lcd_bus build rules

MOD_DIR := $(USERMOD_DIR)

CFLAGS_USERMOD += $(LCD_BUS_CFLAGS)
CFLAGS_USERMOD += -I$(MOD_DIR)
CFLAGS_USERMOD += -I$(MOD_DIR)/common_include
CFLAGS_USERMOD += -I$(MOD_DIR)/sdl_bus
CFLAGS_USERMOD += -Wno-missing-field-initializers

ifneq (,$(findstring unix, $(LV_PORT)))
    CFLAGS_USERMOD += -DMP_PORT_UNIX=1
endif

SRC_USERMOD_C += $(MOD_DIR)/modlcd_bus.c
SRC_USERMOD_C += $(MOD_DIR)/lcd_types.c
SRC_USERMOD_C += $(MOD_DIR)/common_src/i2c_bus.c
SRC_USERMOD_C += $(MOD_DIR)/common_src/i80_bus.c
SRC_USERMOD_C += $(MOD_DIR)/common_src/spi_bus.c
SRC_USERMOD_C += $(MOD_DIR)/common_src/rgb_bus.c
SRC_USERMOD_C += $(MOD_DIR)/sdl_bus/sdl_bus.c
