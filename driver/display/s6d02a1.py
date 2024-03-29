'''


// Color definitions for backwards compatibility with old sketches
// use colour definitions like TFT_BLACK to make sketches more portable
#define S6D02A1_BLACK       0x0000      /*   0,   0,   0 */
#define S6D02A1_NAVY        0x000F      /*   0,   0, 128 */
#define S6D02A1_DARKGREEN   0x03E0      /*   0, 128,   0 */
#define S6D02A1_DARKCYAN    0x03EF      /*   0, 128, 128 */
#define S6D02A1_MAROON      0x7800      /* 128,   0,   0 */
#define S6D02A1_PURPLE      0x780F      /* 128,   0, 128 */
#define S6D02A1_OLIVE       0x7BE0      /* 128, 128,   0 */
#define S6D02A1_LIGHTGREY   0xC618      /* 192, 192, 192 */
#define S6D02A1_DARKGREY    0x7BEF      /* 128, 128, 128 */
#define S6D02A1_BLUE        0x001F      /*   0,   0, 255 */
#define S6D02A1_GREEN       0x07E0      /*   0, 255,   0 */
#define S6D02A1_CYAN        0x07FF      /*   0, 255, 255 */
#define S6D02A1_RED         0xF800      /* 255,   0,   0 */
#define S6D02A1_MAGENTA     0xF81F      /* 255,   0, 255 */
#define S6D02A1_YELLOW      0xFFE0      /* 255, 255,   0 */
#define S6D02A1_WHITE       0xFFFF      /* 255, 255, 255 */
#define S6D02A1_ORANGE      0xFD20      /* 255, 165,   0 */
#define S6D02A1_GREENYELLOW 0xAFE5      /* 173, 255,  47 */
#define S6D02A1_PINK        0xF81F


// Delay between some initialisation commands
#define TFT_INIT_DELAY 0x80


// Generic commands used by TFT_eSPI.cpp
#define TFT_NOP     0x00
#define TFT_SWRST   0x01

#define TFT_INVOFF  0x20
#define TFT_INVON   0x21

#define TFT_DISPOFF 0x28
#define TFT_DISPON  0x29

#define TFT_CASET   0x2A
#define TFT_PASET   0x2B
#define TFT_RAMWR   0x2C

#define TFT_RAMRD   0x2E
#define TFT_IDXRD   0x00 //0xDD // ILI9341 only, indexed control register read

#define TFT_MADCTL  0x36
#define TFT_MAD_MY  0x80
#define TFT_MAD_MX  0x40
#define TFT_MAD_MV  0x20
#define TFT_MAD_ML  0x10
#define TFT_MAD_BGR 0x08
#define TFT_MAD_MH  0x04
#define TFT_MAD_RGB 0x00



	// Initialization commands for S6D02A1 screens
	static const uint8_t S6D02A1_cmds[] PROGMEM =
	{
	29,
	0xf0,	2,	0x5a, 0x5a,				// Excommand2
	0xfc,	2,	0x5a, 0x5a,				// Excommand3
	0x26,	1,	0x01,					// Gamma set
	0xfa,	15,	0x02, 0x1f,	0x00, 0x10,	0x22, 0x30, 0x38, 0x3A, 0x3A, 0x3A,	0x3A, 0x3A,	0x3d, 0x02, 0x01,	// Positive gamma control
	0xfb,	15,	0x21, 0x00,	0x02, 0x04,	0x07, 0x0a, 0x0b, 0x0c, 0x0c, 0x16,	0x1e, 0x30,	0x3f, 0x01, 0x02,	// Negative gamma control
	0xfd,	11,	0x00, 0x00, 0x00, 0x17, 0x10, 0x00, 0x01, 0x01, 0x00, 0x1f, 0x1f,							// Analog parameter control
	0xf4,	15, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3f, 0x3f, 0x07, 0x00, 0x3C, 0x36, 0x00, 0x3C, 0x36, 0x00,	// Power control
	0xf5,	13, 0x00, 0x70, 0x66, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x6d, 0x66, 0x06,				// VCOM control
	0xf6,	11, 0x02, 0x00, 0x3f, 0x00, 0x00, 0x00, 0x02, 0x00, 0x06, 0x01, 0x00,							// Source control
	0xf2,	17, 0x00, 0x01, 0x03, 0x08, 0x08, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x04, 0x08, 0x08,	//Display control
	0xf8,	1,	0x11,					// Gate control
	0xf7,	4, 0xc8, 0x20, 0x00, 0x00,	// Interface control
	0xf3,	2, 0x00, 0x00,				// Power sequence control
	0x11,	TFT_INIT_DELAY, 50,					// Wake
	0xf3,	2+TFT_INIT_DELAY, 0x00, 0x01, 50,	// Power sequence control
	0xf3,	2+TFT_INIT_DELAY, 0x00, 0x03, 50,	// Power sequence control
	0xf3,	2+TFT_INIT_DELAY, 0x00, 0x07, 50,	// Power sequence control
	0xf3,	2+TFT_INIT_DELAY, 0x00, 0x0f, 50,	// Power sequence control
	0xf4,	15+TFT_INIT_DELAY, 0x00, 0x04, 0x00, 0x00, 0x00, 0x3f, 0x3f, 0x07, 0x00, 0x3C, 0x36, 0x00, 0x3C, 0x36, 0x00, 50,	// Power control
	0xf3,	2+TFT_INIT_DELAY, 0x00, 0x1f, 50,	// Power sequence control
	0xf3,	2+TFT_INIT_DELAY, 0x00, 0x7f, 50,	// Power sequence control
	0xf3,	2+TFT_INIT_DELAY, 0x00, 0xff, 50,	// Power sequence control
	0xfd,	11, 0x00, 0x00, 0x00, 0x17, 0x10, 0x00, 0x00, 0x01, 0x00, 0x16, 0x16,							// Analog parameter control
	0xf4,	15, 0x00, 0x09, 0x00, 0x00, 0x00, 0x3f, 0x3f, 0x07, 0x00, 0x3C, 0x36, 0x00, 0x3C, 0x36, 0x00,	// Power control
	0x36,	1, 0xC8,					// Memory access data control
	0x35,	1, 0x00,					// Tearing effect line on
	0x3a,	1+TFT_INIT_DELAY, 0x05, 150,			// Interface pixel control
	0x29,	0,							// Display on
	0x2c,	0							// Memory write
	};

'''