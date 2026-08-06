[![Unix build](https://github.com/lvgl-micropython/lvgl_micropython/actions/workflows/unix.yml/badge.svg)](https://github.com/lvgl-micropython/lvgl_micropython/actions/workflows/unix.yml)
[![macOS build](https://github.com/lvgl-micropython/lvgl_micropython/actions/workflows/macOS.yml/badge.svg)](https://github.com/lvgl-micropython/lvgl_micropython/actions/workflows/macOS.yml)


***IMPORTANT READ ME FIRST***

* DO NOT use any information from the official binding and try to use that when compiling this binding it is not going to work
* DO NOT add any submodule initilization commands when cloning the repo or any any point after the repo has been cloned.
  To clone and build this is how it's done.
  ```
  git clone https://github.com/lvgl-micropython/lvgl_micropython
  cd lvgl_micropython
  python3 make.py esp32 ......
  ```
* If you want to update to the current master then delete your local copy and clone it again from scratch.



# LVGL binding for Micropython
______________________________


This project is a spinoff of the 
[lv_micropython](https://github.com/lvgl/lv_micropython)
 and 
[lv_binding_micropython](https://github.com/lvgl/lv_binding_micropython) 
projects. The goal of this project is to make it easier to compile, create a common API so 
it is easy to add new drivers and to support more connection topologies to displays and input devices.


***What is MicroPython?***

[MicroPython](https://micropython.org) is just how it sounds. It is a micro version of Python. It is written to run on microcontrollers
It has a small memory footprint and small binary size as well as provides access to the hardware
related bits of a microcontroller. 

***What is LVGL?***

[LVGL](https://lvgl.io) is a graphics framework written for C99. It is also written to run on resource constrained devices.
It is a feature rich framework that provides a plethora of different controls (widgets) as well as the ability
to make your owmn custom controls. 

***What is a binding?***

A Binding is code that encapsulates code written in one programming language so it is accessable from another 
programming language. It is best to think of it as a translator, in the case of this project it translates Python 
to C99 and vice versa. It allows us access to the LVGL code by using the Python programming language.

<br>

## *Important Update*

I have altered how the RGBBus driver works. Due to low framerates from LVGL needing to render the whole screen 
each time a small change is made and LVGL also having to keep the 2 frame buffers in sync I have decided to try 
and bring a little bit of my coding ability to the show to see if I am able to overcome some of the performance issues.

This comes at the cost of additional memory but due to the buffers needing to reside in SPIRAM because of their size 
I figured what's a couple hundred K more. What I have done is this.

The 2 full frame buffers are no longer accessable to the user. These are kept tucked away in C code. The user is able to 
allocate partial buffers of any size they want. I have not messed about with this to see if there is a sweet spot with the 
size but I would imagine that 1/10 the display size is a good starting point. I am running a task on the second core of the ESP32
and in that task is where the buffer copying takes place. This is ideal because it is able to offload that work so there is no 
drop in performance in the user code. MicroPython only uses one core of the ESP32 and that is what makes this an ideal thing to do. 

If you use 2 partial buffers while one of being copied to the full frame buffer LVGL is able to fill the other partial buffer.
Another nifty thing I have done is I am handling the rotation of the screen in that task as well. This should provide much better 
performance than having LVGL handle the rotation.

So make sure when you are creating the frame buffers for the RGB display that you make them a fraction of the size of what they 
used to be.

## Table of Contents

- [*Supported display and touch hardware*](#supported-display-and-touch-hardware)
  - [Supported Display IC's](#supported-display-ic's)
  - [Supported Touch IC's](#supported-touch-ic's)
  - [Special use drivers](#special-use-drivers)
- [*Build Instructions*](#build-instructions)
  - [*Requirements*](#requirements)
    - [Compiling for ESP32:](#compiling-for-esp32)
    - [Compiling for RP2:](#compiling-for-rp2)
    - [Compiling for STM32:](#compiling-for-stm32)
    - [Compiling for Ubuntu (Linux):](#compiling-for-ubuntu-linux)
    - [Compiling for macOS :](#compiling-for-macos)
    - [Compiling for Windows:](#compiling-for-windows)
  - [*Command line syntax/parameters*](#command-line-syntax/parameters)
    - [*Build Target (required)*](#build-target-(required))
    - [*Build Options (optional)*](#build-options-(optional))
    - [*Target Options (optional)*](#target-options-(optional))
      - [*Model/Variant*](#model/variant)
      - [*Model/Variant specific options*](#model/variant-specific-options)
        - [*ESP32 options*](#esp32-options)
          - [*Custom Boards*](https://github.com/lvgl-micropython/lvgl_micropython/tree/main/custom_board_and_toml_examples/README.md#custom-boards)
          - [*TOML Example*](https://github.com/lvgl-micropython/lvgl_micropython/tree/main/custom_board_and_toml_examples/README.md#toml-example)
    - [*Global Options (optional)*](#global-options-(optional))
      - [*Input/Output*](#input/output)
      - [*Other global options*](#other-global-options)
  - [*Example build commands*](#example-build-commands)
- [*Python code examples*](#python-code-examples)
  - [*Unix/macOS*](#unix/macos)
  - [*MCU*](#mcu)
    - [*I8080 display with I2C touch input*](#i8080-display-with-i2c-touch-input)
    - [*SPI bus with SPI touch (same SPI bus)*](#spi-bus-with-spi-touch-(same-spi-bus))



## *Supported display and touch hardware*
_____________________________________________

### Supported Display IC's
  * ICs not listed below can often be handled with generic drivers like "rgb_display"
  * GC9A01
  * HX8357B
  * HX8357D
  * ILI9163
  * ILI9225
  * ILI9341
  * ILI9481
  * ILI9486
  * ILI9488
  * LT768x \**WIP*\*
  * R61581
  * RA8876 \**WIP*\*
  * RM68120
  * RM68140
  * S6D02A1
  * SSD1351
  * SSD1963_480
  * SSD1963_800
  * SSD1963_800ALT
  * SSD1963_800BD
  * ST7701S \**WIP*\*
  * ST7735B
  * ST7735R_Red
  * ST7735R_Green
  * ST7789
  * ST7796

### Supported Touch IC's
  * CST816S
  * FT5x06
  * FT5x16
  * FT5x26
  * FT5x36
  * FT5x46
  * FT6x06
  * FT6x36
  * GT911
  * STMPE610
  * XPT2046

### Special use drivers
  * SDL2 \**Only for the unix and macOS ports*\* 


<br>

## *Build Instructions*
_______________________

I have changed the design of the binding so it is no longer a dependancy of 
MicroPython. Instead MicroPython is now a dependency of the binding. By doing 
this I have simplified the process up updating the MicroPython version. Only 
small changes are now needed to support newer versions of MicroPython.

In order to make this all work I have written a Python script that handles
Building the binding. The only prerequesits are that you have a C compiler 
installed (gcc, clang, msvc) and the necessary support libs.

<br>

### *Requirements*
_________________

To compile you will need Python >= 3.10 for for all build types.


#### Compiling for ESP32:

  * Ubuntu (Linux): you can install all of these using `apt-get install` 
    * build-essential
    * cmake
    * ninja-build
    * python
    * python3-venv
    * libusb-1.0-0-dev
    
  * macOS
    * `xcode-select -–install`
    * `brew install cmake`
    * `brew install ninja`
    * `brew install python`


#### Compiling for RP2:

  * Ubuntu (Linux): you can install all of these using `apt-get install` 
    * build-essential
    * cmake
    * ninja-build
    * python
    * gcc-arm-none-eabi 
    * libnewlib-arm-none-eabi
  
  * macOS
    * `command xcode-select–install`
    * `brew install make`
    * `brew install cmake`
    * `brew install ninja`
    * `brew install python`
    * `brew install armmbed/formulae/arm-none-eabi-gcc`

  * Windows
    * Not yet supported


#### Compiling for STM32:

  * Ubuntu (Linux): you can install all of these using `apt-get install` 
    * gcc-arm-none-eabi 
    * libnewlib-arm-none-eabi: maybe??
    * build-essential
    * ninja-build
    * python
  
  * macOS
    * `command xcode-select–install`
    * `brew install make`
    * `brew install ninja`
    * `brew install python`
    * `brew install armmbed/formulae/arm-none-eabi-gcc`

  * Windows
    * Not yet supported


#### Compiling for Ubuntu (Linux):

  use `apt-get install {requirements}` for Ubuntu like Linux variants. 

  * build-essential 
  * libffi-dev 
  * pkg-config
  * cmake
  * ninja-build
  * gnome-desktop-testing
  * libasound2-dev
  * libpulse-dev   
  * libaudio-dev
  * libjack-dev
  * libsndio-dev
  * libx11-dev
  * libxext-dev
  * libxrandr-dev
  * libxcursor-dev
  * libxfixes-dev
  * libxi-dev
  * libxss-dev
  * libxkbcommon-dev
  * libdrm-dev
  * libgbm-dev 
  * libgl1-mesa-dev
  * libgles2-mesa-dev
  * libegl1-mesa-dev
  * libdbus-1-dev
  * libibus-1.0-dev
  * libudev-dev
  * fcitx-libs-dev
  * libpipewire-0.3-dev
  * libwayland-dev   
  * libdecor-0-dev


#### Compiling for macOS:

  * `command xcode-select–install`
  * `brew install libffi` 
  * `brew install ninja`
  * `brew install make`
  * `brew install SDL2`


#### Compiling for Windows:

  * Not yet supported

<br>


### *Command line syntax/parameters*
____________________________________

    python3 make.py {build target} {build options} {target options} {global options}

<br>

#### *Build Target (required)*

This is a required option and it is positional. It must be the first option provided.
Choices are:

  * `esp32`: Espressif ESP32 line of MCU's
  * `macOS`: Compile to run on macOS
    NOTE: MUST be compiled on the same computer it is going to run on
  * `stm32`: ST Microprocessors line of MCU's
  * `unix`: Compile to run on unix
    NOTE: MUST be compiled on the same computer it is going to run on
  * `rp2`: Raspberry Pi Pico 2 MCU
  * `renesas-ra`: Renesas RA line of MCU's
  * `nrf`: Nordic Semiconductor MCU's
  * `mimxrt`: NXP i.MX RT line of MCU's
  * `samd`: Microchip Technology SAM D line of MCU's

<br>

#### *Build Options (optional)*

This is a positoional argument and it must be the second one in the build command 
if it is used. Choices are:

  * `clean`: This flat out deletes the build folder. It will only error if the user doesn't have 
    permission to delete the files in the folder. So if the clean fails run the build using `sudo`
    Make is instructed to perform a clean prior to every build so this really only needs to be used 
    if there is some kind of an issue the make's clean is not cleaning out. This is also how you clean 
    mpy-cross.  

<br>

#### *Target Options (optional)*

Target options is broken down into 2 sections

    python3 make.py {build target} {build options} {{model/variant} {model/variant specific options}} {global options}


##### *Model/Variant*

The model is the processor model being used or the build type. The build type is what is 
specified when compiling to run  on macOS or Unix.

When compiling for macOS or Unix you are able to specify the build type. That is done by using
the `VARIANT` option. The syntax for this option is `VARIANT={build type}`

Here are the available build types:

  * `coverage`
  * `minimal`
  * `nanbox`
  * `standard` (default)


When compiling for all others you use the `BOARD` option. The symntax for this option 
is `BOARD={board name}`. Some "boards" are generic and can have different variants. To specify
what board variamnmt is being used you use the following option, `BOARD_VARIANT={variant}`.

This is a list of the boards that MicroPython supports. Some of these boards might not have 
enough available program storage or RAM to be able to run the binding. I will at some point look 
at the specs for each of them to see if they will be able to run this binding.

Any sub items listed under a board is a variant that is available for that board.

NOTE: You cannot specify a variant unless the board has been specified.

  * esp32: 
    * ARDUINO_NANO_ESP32
    * ESP32_GENERIC
      * D2WD
      * OTA
      * SPIRAM
      * UNICORE
    * ESP32_GENERIC_C3
    * ESP32_GENERIC_S2
    * ESP32_GENERIC_S3
      * SPIRAM_OCT
    * LILYGO_TTGO_LORA32
    * LOLIN_C3_MINI
    * LOLIN_S2_MINI
    * LOLIN_S2_PICO
    * M5STACK_ATOM
    * OLIMEX_ESP32_POE
    * SIL_WESP32
    * UM_FEATHERS2
    * UM_FEATHERS2NEO
    * UM_FEATHERS3
    * UM_NANOS3
    * UM_PROS3
    * UM_TINYPICO
    * UM_TINYS2
    * UM_TINYS3
    * UM_TINYWATCHS3
       
  * stm32:
    * ADAFRUIT_F405_EXPRESS
    * ARDUINO_GIGA
    * ARDUINO_NICLA_VISION
    * ARDUINO_PORTENTA_H7
    * B_L072Z_LRWAN1
    * B_L475E_IOT01A
    * CERB40
    * ESPRUINO_PICO
    * GARATRONIC_NADHAT_F405
    * GARATRONIC_PYBSTICK26_F411
    * HYDRABUS
    * LEGO_HUB_NO6
    * LEGO_HUB_NO7
    * LIMIFROG
    * MIKROE_CLICKER2_STM32
    * MIKROE_QUAIL
    * NETDUINO_PLUS_2
    * NUCLEO_F091RC
    * NUCLEO_F401RE
    * NUCLEO_F411RE
    * NUCLEO_F412ZG
    * NUCLEO_F413ZH
    * NUCLEO_F429ZI
    * NUCLEO_F439ZI
    * NUCLEO_F446RE
    * NUCLEO_F722ZE
    * NUCLEO_F746ZG
    * NUCLEO_F756ZG
    * NUCLEO_F767ZI
    * NUCLEO_G0B1RE
    * NUCLEO_G474RE
    * NUCLEO_H563ZI
    * NUCLEO_H723ZG
    * NUCLEO_H743ZI
    * NUCLEO_H743ZI2
    * NUCLEO_L073RZ
    * NUCLEO_L152RE
    * NUCLEO_L432KC
    * NUCLEO_L452RE
    * NUCLEO_L476RG
    * NUCLEO_L4A6ZG
    * NUCLEO_WB55
    * NUCLEO_WL55
    * OLIMEX_E407
    * OLIMEX_H407
    * PYBD_SF2
    * PYBD_SF3
    * PYBD_SF6
    * PYBLITEV10
    * PYBV10
    * PYBV11
    * PYBV3
    * PYBV4
    * SPARKFUN_MICROMOD_STM32
    * STM32F411DISC
    * STM32F429DISC
    * STM32F439
    * STM32F4DISC
    * STM32F769DISC
    * STM32F7DISC
    * STM32H573I_DK
    * STM32H7B3I_DK
    * STM32L476DISC
    * STM32L496GDISC
    * USBDONGLE_WB55
    * VCC_GND_F407VE
    * VCC_GND_F407ZG
    * VCC_GND_H743VI
  
  * rp2:
    * ADAFRUIT_FEATHER_RP2040
    * ADAFRUIT_ITSYBITSY_RP2040
    * ADAFRUIT_QTPY_RP2040
    * ARDUINO_NANO_RP2040_CONNECT
    * GARATRONIC_PYBSTICK26_RP2040
    * NULLBITS_BIT_C_PRO
    * PIMORONI_PICOLIPO_16MB
    * PIMORONI_PICOLIPO_4MB
    * PIMORONI_TINY2040
    * POLOLU_3PI_2040_ROBOT
    * POLOLU_ZUMO_2040_ROBOT
    * RPI_PICO
    * RPI_PICO_W
    * SIL_RP2040_SHIM
    * SPARKFUN_PROMICRO
    * SPARKFUN_THINGPLUS
    * W5100S_EVB_PICO
    * W5500_EVB_PICO
    * WEACTSTUDIO
      * FLASH_2M
      * FLASH_4M
      * FLASH_8M
      
    * renesas-ra:
      * ARDUINO_PORTENTA_C33
      * EK_RA4M1
      * EK_RA4W1
      * EK_RA6M1
      * EK_RA6M2
      * RA4M1_CLICKER
      * VK_RA6M5
      
    * nrf:
      * ACTINIUS_ICARUS
      * ARDUINO_NANO_33_BLE_SENSE
      * ARDUINO_PRIMO
      * BLUEIO_TAG_EVIM
      * DVK_BL652
      * EVK_NINA_B1
      * EVK_NINA_B3
      * FEATHER52
      * IBK_BLYST_NANO
      * IDK_BLYST_NANO
      * MICROBIT
      * NRF52840_MDK_USB_DONGLE
      * PARTICLE_XENON
      * PCA10000
      * PCA10001
      * PCA10028
      * PCA10031
      * PCA10040
      * PCA10056
      * PCA10059
      * PCA10090
      * SEEED_XIAO_NRF52
      * WT51822_S4AT 

    * mimxrt:
      * ADAFRUIT_METRO_M7
      * MIMXRT1010_EVK
      * MIMXRT1015_EVK
      * MIMXRT1020_EVK
      * MIMXRT1050_EVK
      * MIMXRT1060_EVK
      * MIMXRT1064_EVK
      * MIMXRT1170_EVK
      * OLIMEX_RT1010
      * SEEED_ARCH_MIX
      * TEENSY40
      * TEENSY41

    * samd:
      * ADAFRUIT_FEATHER_M0_EXPRESS
      * ADAFRUIT_FEATHER_M4_EXPRESS
      * ADAFRUIT_ITSYBITSY_M0_EXPRESS
      * ADAFRUIT_ITSYBITSY_M4_EXPRESS
      * ADAFRUIT_METRO_M4_EXPRESS
      * ADAFRUIT_TRINKET_M0
      * MINISAM_M4
      * SAMD21_XPLAINED_PRO
      * SEEED_WIO_TERMINAL
      * SEEED_XIAO_SAMD21
      * SPARKFUN_SAMD51_THING_PLUS


##### *Model/Variant specific options*
______________________________________


###### *ESP32 options*

Common options that are available across all esp32 targets:

* `BAUD={bits per second}`: How fast to flash the firmware, `deploy` must also be set to use this
* `PORT={serial port}`: Port the ESP is connected to, `deploy` must also be set to use this
* `deploy`: After building flash the firmware, `PORT` and `BAUD` are optional. The speed will default 
            to whatever the ESP-IDF is set to and there will be an attempt at detecting the port automatically
* `--skip-partition-resize`: If you do not want the build system to resize the application partition automatically.
* `--partition-size={app partition size}`: Manually set the application partition size. This is something you want 
                                           to do when using ota firmware updates. the size of the firmware may change 
                                           so setting the application partition to be larger than what the actual firmware  
                                           size is is something I recommend doing. Having to modify the partition sizes over 
                                           the air is not possible to do.   
* `--optimize-size`: The build is set to optimize the firmware for performance. If you find that space is more of an issue
                     then set this to get a smaller firmware size
* `--debug`: Enables debugging output from the ESP-IDF
* `--ccache`: This will speed up the build if the application partition size gets resized. It requires the `ccache` library to be installed
* `--flash-size={4, 8, 16, 32, 64 or 128}`: Sets the flash size that you have available on your ESP32
* `--ota`: Add this flag if you wanbt to do OTA updates. This creates 2 application partitions that are the same size. 
* `--dual-core-threads`: (Experimental) MicroPython is written so that the user is only able to run code on a single core of the ESP32.
                         That is very limiting. This option allows code to run on both CPU cores. Be warned this option also disables the GIL
                         so care must be given to accessing global variables. You need to put nlocks in place to keep the memory from getting 
                         corrupted. You do not get to decide what core to use. That is automatically done based on the load that is on the cores.
* `--task-stack-size={stack size in bytes}`: Sets the default stack size for threads
* `CONFIG_*={value}`: You can alter the config settings of the esp-idf by using these settings. Refer to the ESP-IDF documentation
                      for further information
* `--uart-repl-bitrate={baud/bitrate}`: This changes the connection speed for the serial connection when using the UART REPL.
                                        This is a nice feature to use when transferring large files to the ESP32. The highest 
                                        speed I have been able to set it to is 921600, you might be able to set it higher depending
                                        on the UART to USB bridge IC used and the type of physical connection. 
* `--enable-uart-repl={y/n}`: This allows you to turn on and off the UART based REPL. You will wany to set this of you use USB-CDC or JTAG for the REPL output


Options specific to the ESP32-S3 processors:

* `--octal-flash`: Set this if you have octal SPI flash

Options specific to the ESP32-S2, ESP32-S3, ESP32-C3 and ESP32-C6 processors:

* `--enable-cdc-repl={y/n}`: Enable/disable REPL output over CDC on the USB pins
* `--enable-jtag-repl={y/n}`: Enable/disable REPL output over JTAG on the USB pins

* `--custom-board-path={path to custom board}`: [Custom Board](https://github.com/lvgl-micropython/lvgl_micropython/tree/main/custom_board_and_toml_examples/README.md#custom-boards) 
* `--toml={path to .toml file}`: [TOML Example](https://github.com/lvgl-micropython/lvgl_micropython/tree/main/custom_board_and_toml_examples/README.md#toml-example)


<br>

#### *Global Options (optional)*
________________________________

These are options that are available across all targets, boards and board variants.
The global options are broken down into 2 secions

    python3 make.py {build target} {build options} {target options} {{input/output} {other}}

<br>

##### *Input/Output*

  * `DISPLAY={ic model or path}`: Model number of the display driver that is located in `api_drivers/common_api_drivers/display`
             or it can be the absolute path to a custom driver you have written. This must be the 
             path to the folder that contains the driver files.
  * `INDEV={ic model or path}`: Model number of indev driver that is located in `api_drivers/common_api_drivers/indev`
           or it can be the absolute path to your own custom driver (with the .py extension)

The above options are able to be repeated if you want to include multiple drivers.

<br>

##### *Other global options*

  * `LV_CFLAGS="{lvgl compile options}"`: additional compiler flags that get passed to the LVGL build only.
  * `FROZEN_MANIFEST={path/to/manifest.py}`: path to a custom frozen manifest file


<br>


### *Example build commands*
___________________________

Build for an ESP32-S3 processor with Octal SPIRAM and the given display and input drivers

    python3 make.py esp32 BOARD=ESP32_GENERIC_S3 BOARD_VARIANT=SPIRAM_OCT DISPLAY=st7796 INDEV=gt911

If you have problems on builds after the first one, you can try adding the "clean" keyword to clear out residue from previous builds.

I will provide directions on how to use the driver framework and also the drivers that are included
with the binding in the coming weeks.

<br>

SDL fpr Unix is working properly. Make sure you review the requirements needed to compile for unix!!!
The build system compiles the latest version of SDL2 so the list is pretty long for the requirements.

To build for Unix use the following build command

    python3 make.py unix DISPLAY=sdl_display INDEV=sdl_pointer


Couple of notes:

  * **DO NOT** enable LV_USE_DRAW_SDL, I have not written code to allow for it's use (yet).



## *Python code examples*
_________________________

### *Unix/macOS*

```py
from micropython import const  # NOQA
import lcd_bus  # NOQA


_WIDTH = const(480)
_HEIGHT = const(320)

bus = lcd_bus.SDLBus(flags=0)

buf1 = bus.allocate_framebuffer(_WIDTH * _HEIGHT * 3, 0)

import lvgl as lv  # NOQA
import sdl_display  # NOQA


display = sdl_display.SDLDisplay(
    data_bus=bus,
    display_width=_WIDTH,
    display_height=_HEIGHT,
    frame_buffer1=buf1,
    color_space=lv.COLOR_FORMAT.RGB888
)
display.init()

import sdl_pointer
import task_handler

mouse = sdl_pointer.SDLPointer()

# the duration needs to be set to 5 to have a good response from the mouse.
# There is a thread that runs that facilitates double buffering. 
th = task_handler.TaskHandler(duration=5)

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x000000), 0)

slider = lv.slider(scrn)
slider.set_size(300, 25)
slider.center()
```

The touch screen drivers will handle the rotation that you set to the display.
There is a single caviat to this. You MUST set up and initilize the display then 
create the touch drivers and after that has been done you can set the rotation.
The touch driver must exist prior to the display rotation being set.

For the ESP32 SOC's there is NVRAM that is available to store data in. That 
data is persistant between restarts of the ESP32. This feature is pur to use to 
store calibration data for the touch screen. In the exmaple below it shows how 
to properly create a display driver and touch driver and how to set the rotation 
and also the calibration storage.

<br>

### *MCU*
_________


#### *I8080 display with I2C touch input*

```py
import lcd_bus
from micropython import const

# display settings
_WIDTH = const(320)
_HEIGHT = const(480)
_BL = const(45)
_RST = const(4)
_DC = const(0)
_WR = const(47)
_FREQ = const(20000000)
_DATA0 = const(9)
_DATA1 = const(46)
_DATA2 = const(3)
_DATA3 = const(8)
_DATA4 = const(18)
_DATA5 = const(17)
_DATA6 = const(16)
_DATA7 = const(15)
_BUFFER_SIZE = const(30720)

_SCL = const(5)
_SDA = const(6)
_TP_FREQ = const(100000)

display_bus = lcd_bus.I80Bus(
    dc=_DC,
    wr=_WR,
    freq=_FREQ,
    data0=_DATA0,
    data1=_DATA1,
    data2=_DATA2,
    data3=_DATA3,
    data4=_DATA4,
    data5=_DATA5,
    data6=_DATA6,
    data7=_DATA7
)

fb1 = display_bus.allocate_framebuffer(_BUFFER_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)
fb2 = display_bus.allocate_framebuffer(_BUFFER_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)

import st7796  # NOQA
import lvgl as lv  # NOQA

lv.init()

display = st7796.ST7796(
    data_bus=display_bus,
    frame_buffer1=fb1,
    frame_buffer2=fb2,
    display_width=_WIDTH,
    display_height=_HEIGHT,
    backlight_pin=_BL,
    # reset=_RST,
    # reset_state=st7796.STATE_LOW,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=st7796.BYTE_ORDER_BGR,
    rgb565_byte_swap=True,
)

import i2c  # NOQA
import task_handler  # NOQA
import ft6x36  # NOQA

display.init()

i2c_bus = i2c.I2C.Bus(host=0, scl=_SCL, sda=_SDA, freq=_TP_FREQ, use_locks=False)
touch_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=ft6x36.I2C_ADDR, reg_bits=ft6x36.BITS)

indev = ft6x36.FT6x36(touch_dev)

display.invert_colors()

if not indev.is_calibrated:
    display.set_backlight(100)
    indev.calibrate()

# you want to rotate the display after the calibration has been done in order
# to keep the corners oriented properly.
display.set_rotation(lv.DISPLAY_ROTATION._90)

display.set_backlight(100)

th = task_handler.TaskHandler()

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x000000), 0)

slider = lv.slider(scrn)
slider.set_size(300, 50)
slider.center()

label = lv.label(scrn)
label.set_text('HELLO WORLD!')
label.align(lv.ALIGN.CENTER, 0, -50)
```

<br>

#### *SPI bus with SPI touch (same SPI bus)*
____________________________________________

```py
import lcd_bus
from micropython import const
import machine


# display settings
_WIDTH = const(320)
_HEIGHT = const(480)
_BL = const(45)
_RST = const(4)
_DC = const(0)

_MOSI = const(11)
_MISO = const(13)
_SCK = const(12)
_HOST = const(1)  # SPI2

_LCD_CS = const(10)
_LCD_FREQ = const(80000000)

_TOUCH_CS = const(18)
_TOUCH_FREQ = const(10000000)

spi_bus = machine.SPI.Bus(
    host=_HOST,
    mosi=_MOSI,
    miso=_MISO,
    sck=_SCK
)

display_bus = lcd_bus.SPIBus(
    spi_bus=spi_bus,
    freq=_LCD_FREQ,
    dc=_DC,
    cs=_LCD_CS,
)

# we are going to let the display driver sort out the best freame buffer size and where to allocate it to.
# fb1 = display_bus.allocate_framebuffer(_BUFFER_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)
# fb2 = display_bus.allocate_framebuffer(_BUFFER_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)

import st7796  # NOQA
import lvgl as lv  # NOQA


display = st7796.ST7796(
    data_bus=display_bus,
    display_width=_WIDTH,
    display_height=_HEIGHT,
    backlight_pin=_BL,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=st7796.BYTE_ORDER_RGB,
    rgb565_byte_swap=True,
)

import task_handler  # NOQA
import xpt2046  # NOQA

display.set_power(True)
display.init()
display.set_backlight(100)

touch_dev = machine.SPI.Device(
    spi_bus=spi_bus,
    freq=_TOUCH_FREQ,
    cs=_TOUCH_CS
)

indev = xpt2046.XPT2046(touch_dev)

th = task_handler.TaskHandler()

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x000000), 0)

slider = lv.slider(scrn)
slider.set_size(300, 50)
slider.center()

label = lv.label(scrn)
label.set_text('HELLO WORLD!')
label.align(lv.ALIGN.CENTER, 0, -50)
```

You are able to force the calibration at any time by calling `indev.calibrate()` 
regardless of what `indev.is_calibrate` returns. This makes it possible to redo 
the calibration by either using a pin that you can check the state of or through
a button in your UI that you provide to the user.

Thank again and enjoy!!

<br>
<br>

***NOTE***: SPI host 0 on the ESP32 is reserved for use with SPIRAM and flash. 

<br>
<br>

***NOT USED AT THIS TIME***
_____________________________________________________________________


Bit orders are a tuple of durations. The first 2 numbers define a bit as 0 and the second 2 define a bit as 1. Negitive numbers are the duration to hold low and positive are for how long to hold high
"Res" or "Reset" is sent at the end of the data. 

| Name                                                                        |  Bit 0<br/>Duration 1   | Bit 0<br/>Duration 2 | Bit 1<br/>Duration 1  | Bit 1<br/>Duration 2 |  Res  |  Order  |
|:----------------------------------------------------------------------------|:-----------------------:|:--------------------:|:---------------------:|:--------------------:|:-----:|:-------:|
| APA105<br/>APA109<br/>APA109<br/>SK6805<br/>SK6812<br/>SK6818               |           300           |         -900         |          600          |         -600         | -800  |   GRB   |
| WS2813                                                                      |           300           |         -300         |          750          |         -300         | -300  |   GRB   |
| APA104                                                                      |           350           |        -1360         |         1360          |         -350         | -240  |   RGB   |
| SK6822                                                                      |           350           |        -1360         |         1360          |         -350         | -500  |   RGB   |
| WS2812                                                                      |           350           |         -800         |          700          |         -600         | -5000 |   GRB   |
| WS2818A<br/>WS2818B<br/>WS2851<br/>WS2815B<br/>WS2815<br/>WS2811<br/>WS2814 |           220           |         -580         |          580          |         -220         | -280  |   RGB   |
| WS2818                                                                      |           220           |         -750         |          750          |         -220         | -300  |   RGB   |
| WS2816A<br/>WS2816B<br/>WS2816C                                             |           200           |         -800         |          520          |         -480         | -280  |   GRB   |
| WS2812B                                                                     |           400           |         -850         |          800          |         -450         | -5000 |   GRB   |
| SK6813                                                                      |           240           |         -800         |          740          |         -200         | -800  |   GRB   |

<br>

# Projects made with this Binding...

-----------------------------------------------------------

https://github.com/fabse-hack/temp_humidity_micropython_lvgl



