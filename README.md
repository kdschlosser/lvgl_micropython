# LVGL binding for Micropython
______________________________


I have tried to make this as simple as possible for paople to use. 
There are some glitches still in it I am sure. If you come across an issue 
please let me know.

I am still in development mode for the unix port. I am writing an SDL driver 
that conforms To the rest of the driver framework. I have started working on 
writing the frameworks for the different indev (input) types that LVGL supports.
The frameworks are written to make it easier to write display and input drivers
for the binding.

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
Linux

  * build-essential 
  * libffi-dev 
  * pkg-config


Compiling for STM32 unider Linux

  * gcc-arm-none-eabi 
  * libnewlib-arm-none-eabi


OSX 

  * brew install llvm


Windows

  * not supported yet

<br>
 
### *Build Target*
__________________

You are also going to need Python >= 3.10 installed for all builds

There is a single entry point for all builds. That is the make.py script in the
root of the repository.

The first argument is positional and it must be one of the following.

  * esp32
  * windows
  * stm32
  * unix
  * rp2 
  * renesas-ra
  * nrf
  * mimxrt
  * samd


<br>

### *Build Options*
________________________

The next few arguments are optional to some degree.

  * submodules\*\*: collects all needed dependencies to perform the build
  * clean: cleans the build environment
  * mpy_cross\*\*: compiles mpy-cross 
               this is not used for all builds. if it is not supported it will do nothing.


**must be run only one time when the build is intially started. after that you will not need 
to add these arguments. There is internal checking that is done to see if the argument needs to 
be carried out. So you can also optionally leave it there if you want. 

<br>

### *Identifying the MCU board*
_______________________________

The next group of options are going to be port specific, some may have them and some may not.

  * BOARD: The MCU to build for. This follows the same symantics as what MIcroPython uses.
  * BOARD_VARIANT: if there is a variation of the board that it to be compiled for.


I will go into specifics for what what boards and variants are available for a specific port a 
little bit further down.

<br>

### *Additional Arguments*
____________________

  * LV_CFLAGS: additional compiler flags that get passed to the LVGL build only.
  * FROZEN_MANIFEST: path to a custom frozen manifest file
  * DISPLAY: this can either be the file name (less the .py) of a display 
             driver that is in the driver/display folder or it can be the absolute
             path to your own custom driver (with the .py extension)
  * INDEV: this can either be the file name (less the .py) of an indev 
           driver that is in the driver/indev folder or it can be the absolute
           path to your own custom driver (with the .py extension)


<br>

### *ESP32 specific options*
____________________________
  * --skip-partition-resize: do not resize the firmware partition
  * --partition-size: set a custom firmware partition size


<br>

## *Boards & Board Variants*
___________

  * esp32: BOARD=
    * ARDUINO_NANO_ESP32
    * ESP32_GENERIC
      * BOARD_VARIANT=D2WD
      * BOARD_VARIANT=OTA
    * ESP32_GENERIC_C3
    * ESP32_GENERIC_S2
    * ESP32_GENERIC_S3
      * BOARD_VARIANT=SPIRAM_OCT
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

  * windows: VARIANT=
    * dev
    * stndard
    
  * stm32: BOARD=
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

  * unix: VARIANT=
    * coverage
    * minimal
    * nanbox
    * standard
  
  * rp2: BOARD=
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
      * BOARD_VARIANT=FLASH_2M
      * BOARD_VARIANT=FLASH_4M
      * BOARD_VARIANT=FLASH_8M
      
    * renesas-ra: BOARD=
      * ARDUINO_PORTENTA_C33
      * EK_RA4M1
      * EK_RA4W1
      * EK_RA6M1
      * EK_RA6M2
      * RA4M1_CLICKER
      * VK_RA6M5
      
    * nrf: BOARD=
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

    * mimxrt: BOARD=
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

    * samd: BOARD=
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
      

<br>

## *Build Command Examples*
___________________________

build with submodules and mpy_cross

    python3 make.py esp32 submodules clean mpy_cross BOARD=ESP32_GENERIC_S3 BOARD_VARIANT=SPIRAM_OCT DISPLAY=st7796 INDEV=gt911

build without submodules or mpy_cross

    python3 make.py esp32 clean BOARD=ESP32_GENERIC_S3 BOARD_VARIANT=SPIRAM_OCT DISPLAY=st7796 INDEV=gt911


I always recommend building with the clean command, this will ensure you get a good fresh build.

NOTE:
There is a bug in the ESP32 build. The first time around it will fail saying that 
one of the sumbodules is not available. Run the build again with the submodules 
argument in there and then it will build fine. For the life of me I cam not able to locate
where the issue is stemming from. I will find it eventually.

<br>

I will provide directions on how to use the driver framework and also the drivers that are included
with the binding in the coming weeks.

<br>

Thank again and enjoy!!
