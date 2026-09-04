# Copyright (c) 2024 - 2025 Kevin G. Schlosser

import os
import sys
import shutil
from . import spawn
from . import generate_manifest
from . import update_mphalport as _update_mphalport
from . import (
    read_file,
    write_file,
    copy_micropy_updates,
    revert_files,
    scrub_build_folder
)
from argparse import ArgumentParser


mpy_cross_cmd = []
clean_cmd = []
unix_cmd = [
    'make',
    '',
    f'-j {os.cpu_count()}',
    '-C',
]

compile_cmd = []
submodules_cmd = []
heap_size = 4194304
sdl_flags = ''

REAL_PORT = 'unix'


def parse_args(extra_args, lv_cflags, board):
    global heap_size
    global sdl_flags

    unix_argParser = ArgumentParser(prefix_chars='-S')

    unix_argParser.add_argument(
        '--heap-size',
        dest='heap_size',
        help="heap size to use in bytes. Default is 8MiB (8,388,608 bytes). "
             "Must be more than 100KiB (102,104 bytes)",
        default=(2 ** 20) * 8,
        type=int,
        action='store'
    )

    unix_argParser.add_argument(
        'SDL_FLAGS',
        dest='sdl_flags',
        help='flags to pass to the SDL2 compiler',
        default='',
        action='store'
    )
    unix_args, extra_args = unix_argParser.parse_known_args(extra_args)

    if unix_args.heap_size < 102400:
        raise RuntimeError('heap size is too low, must be >= 102,104 bytes')

    heap_size = unix_args.heap_size
    sdl_flags = unix_args.sdl_flags

    return extra_args, lv_cflags, board


variant = None
SCRIPT_PATH = ''


def build_commands(_, extra_args, script_dir, lv_cflags, board):
    global variant

    if board is None:
        board = 'standard'

    variant = board

    unix_cmd.append(f'{script_dir}/lib/micropython/ports/unix')

    if board:
        unix_cmd.append(f'VARIANT={board}')

    unix_cmd.extend(
        [
            f'LV_CFLAGS="{lv_cflags}"',
            f'LV_PORT={REAL_PORT}',
            f'USER_C_MODULES="{script_dir}/ext_mod"',
            (
                '"CFLAGS_EXTRA='
                '-Wno-sign-compare '
                '-Wno-unused-function '
                '-Wno-double-promotion '
                '-Wno-unused-command-line-argument '
                '-Wno-missing-field-initializers"'
                # 'export CPPFLAGS="-I/opt/homebrew/opt/libffi/include"'
            )
        ]
    )

    # unix_cmd.extend(extra_args)

    clean_cmd.extend(unix_cmd[:])
    clean_cmd[1] = 'clean'

    compile_cmd.extend(unix_cmd[:])
    compile_cmd.pop(1)

    submodules_cmd.extend(unix_cmd[:])
    submodules_cmd[1] = 'submodules'
    return extra_args


def build_manifest(
    _,
    script_dir,
    lvgl_api,
    displays,
    indevs,
    expanders,
    imus,
    frozen_manifest
):
    global SCRIPT_PATH

    SCRIPT_PATH = script_dir

    _update_mphalport(REAL_PORT)

    manifest_path = 'lib/micropython/ports/unix/variants/manifest.py'

    generate_manifest(script_dir, lvgl_api, manifest_path, displays,
                      indevs, expanders, imus, frozen_manifest)


def force_clean(clean_mpy_cross):
    if clean_mpy_cross:
        cross_clean = mpy_cross_cmd[:]
        cross_clean.insert(1, 'clean')
        spawn(cross_clean)

    spawn(clean_cmd)


def clean():
    path = f'lib/micropython/ports/unix/build-{variant}'
    if not os.path.exists(path):
        return

    for file in os.listdir(path):
        if file == 'SDL':
            continue

        file = os.path.join(path, file)
        try:
            if os.path.isdir(file):
                shutil.rmtree(file)
            else:
                os.remove(file)
        except OSError:
            pass


def _run(c, spinner=False, cmpl=False):
    res, _ = spawn(c, spinner=spinner, cmpl=cmpl)
    if res != 0:
        sys.exit(res)


def build_sdl(addl_commands):
    dst = f'lib/micropython/ports/unix/build-{variant}/SDL'

    if not os.path.exists(dst):
        os.makedirs(dst)
    elif os.path.exists(os.path.join(dst, 'libSDL2.a')):
        return

    cwd = os.getcwd()
    os.chdir(dst)
    cmd_ = [
        [
            f'cmake -DSDL_STATIC=ON -DSDL_SHARED=OFF '
            f'-DCMAKE_BUILD_TYPE=Release {addl_commands} {SCRIPT_PATH}/lib/SDL'
        ],
        [f'cmake --build . --config Release --parallel {os.cpu_count()}']
    ]

    res, _ = spawn(cmd_, cmpl=True)
    if res != 0:
        sys.exit(res)

    os.chdir(cwd)


def submodules():
    if not os.path.exists('lib/SDL/include'):
        print()
        print('collecting SDL2')
        cmd_ = [
            'git',
            'submodule',
            'update',
            '--init',
            '--',
            f'lib/SDL'
        ]
        _run(cmd_)

    # 2.32.8 is the SDL2 maintenance line with "Fixed building on macOS with
    # OpenGL disabled" (libsdl-org/SDL 0b6eff41): 2.30.2 fails to compile
    # against recent Xcode SDKs because SDL_cocoawindow.m messages the
    # forward-declared SDLOpenGLContext when SDL_OPENGL is off, which newer
    # clang treats as an error. Fetch first for clones that predate the tag.
    cmd_ = [
        'cd lib/SDL && git checkout release-2.32.8 2>/dev/null '
        '|| (git fetch --tags && git checkout release-2.32.8)'
    ]
    _run(cmd_)

    return_code, _ = spawn(submodules_cmd)
    if return_code != 0:
        sys.exit(return_code)


if not os.path.exists('micropy_updates/originals/unix'):
    os.makedirs('micropy_updates/originals/unix')


UNIX_MPHAL_PATH = 'lib/micropython/ports/unix/unix_mphal.c'
MPCONFIGVARIANT_COMMON_PATH = (
    'lib/micropython/ports/unix/variants/mpconfigvariant_common.h'
)
INPUT_PATH = 'lib/micropython/ports/unix/input.c'
MODMACHINE_PATH = 'lib/micropython/ports/unix/modmachine.c'
MAIN_PATH = 'lib/micropython/ports/unix/main.c'
MAKEFILE_PATH = 'lib/micropython/ports/unix/Makefile'


def update_makefile():
    data = read_file(REAL_PORT, MAKEFILE_PATH)

    if 'machine_timer.c' not in data:
        code = [
            'modjni.c \\',
            '\tmachine_timer.c \\',
            '\tmachine_sdl.c \\',
            ''
        ]
        data = data.replace('modjni.c \\\n', '\n'.join(code))

        write_file(MAKEFILE_PATH, data)


def update_modmachine():
    data = read_file(REAL_PORT, MODMACHINE_PATH)

    if 'MICROPY_PY_MACHINE_EXTRA_GLOBALS' not in data:
        data += (
            '\n#define MICROPY_PY_MACHINE_EXTRA_GLOBALS    '
            '    { MP_ROM_QSTR(MP_QSTR_Timer), MP_ROM_PTR(&machine_timer_type) }, \n\n'  # NOQA
        # NOQA
        )

        write_file(MODMACHINE_PATH, data)


def update_main():

    data = read_file(REAL_PORT, MAIN_PATH)

    if 'machine_timer.h' not in data:
        code = [
            '#include "input.h"',
            '#include "machine_timer.h"'
        ]
        data = data.replace('#include "input.h"', '\n'.join(code))

    if 'machine_sdl.h' not in data:
        code = [
            '#include "input.h"',
            '#include "machine_sdl.h"'
        ]
        data = data.replace('#include "input.h"', '\n'.join(code))

    if 'machine_timer_deinit_all()' not in data:
        data = data.replace(
            '#if MICROPY_PY_SYS_ATEXIT',
            'machine_timer_deinit_all();\n    #if MICROPY_PY_SYS_ATEXIT'
        )

    if 'deinit_sdl()' not in data:
        data = data.replace(
            '#if MICROPY_PY_SYS_ATEXIT',
            'deinit_sdl();\n    #if MICROPY_PY_SYS_ATEXIT'
        )

    if 'init_sdl()' not in data:
        data = data.replace(
            'mp_init();',
            'mp_init();\n    init_sdl();'
        )

    if '*mp_repl_get_ps3' not in data:
        code = [
            'char *mp_repl_get_ps3(void)',
            '{',
            '    return "";',
            '}',
            '',
            '',
            'static int do_repl(void) {'
        ]

        data = data.replace('static int do_repl(void) {', '\n'.join(code))

    if 'EWOULDBLOCK' not in data:
        code = [
            'if (errno != EWOULDBLOCK) {',
            '                return 0;',
            '            } else {',
            '                while (line == NULL && errno == EWOULDBLOCK) {',
            '                    mp_handle_pending(true);',
            '                    usleep(1000);',
            '                    line = prompt(mp_repl_get_ps3());',
            '                }',
            '                if (line == NULL) return 0;',
            '            }',
        ]

        data = data.replace('// EOF\n            return 0;', '\n'.join(code))

    data = data.split('\n')

    for i, line in enumerate(data):
        if line.startswith('long heap_size ='):
            data[i] = f'long heap_size = {heap_size};'
            break

    data = '\n'.join(data)

    write_file(MAIN_PATH, data)


def update_input():
    data = read_file(REAL_PORT, INPUT_PATH)
    if 'O_NONBLOCK' not in data:
        code = [
            'char *prompt(char *p) {',
            '    int stdin_fd = fileno(stdin);',
            '    int flags = fcntl(stdin_fd, F_GETFL);',
            '    flags |= O_NONBLOCK;',
            '    fcntl(stdin_fd, F_SETFL, flags);',
            ''
        ]

        data = data.replace('char *prompt(char *p) {', '\n'.join(code))
        write_file(INPUT_PATH, data)


def update_unix_mphal():

    data = read_file(REAL_PORT, UNIX_MPHAL_PATH)

    if 'EWOULDBLOCK' not in data:
        code = [
            'int flags = fcntl(STDIN_FILENO, F_GETFL);',
            '    flags |= O_NONBLOCK;',
            '    fcntl(STDIN_FILENO, F_SETFL, flags);',
            '',
            '    for (;;) {',
            '        MP_THREAD_GIL_EXIT();',
            '        ret = read(STDIN_FILENO, &c, 1);',
            '        MP_THREAD_GIL_ENTER();',
            '        if (ret == -1) {',
            '            int err = errno;',
            '',
            '            if (err == EINTR) {',
            '                mp_handle_pending(true);',
            '                continue;',
            '            } else {',
            '                while (ret == -1 && err == EWOULDBLOCK) {',
            '                    mp_handle_pending(true);',
            '                    usleep(1000);',
            '                    ret = read(STDIN_FILENO, &c, 1);',
            '                    if (ret == -1) err = errno;',
            '                }',
            '                if (ret == -1) continue;',
            '                break;',
            '            }',
            '        }',
            '        break;',
            '    }',
            ''
        ]

        data = data.replace(
            'MP_HAL_RETRY_SYSCALL(ret, read(STDIN_FILENO, &c, 1), {});',
            '\n'.join(code)
        )

        write_file(UNIX_MPHAL_PATH, data)


def update_mpconfigvariant_common():

    data = read_file(REAL_PORT, MPCONFIGVARIANT_COMMON_PATH)

    if (
        '#define MICROPY_MALLOC_USES_ALLOCATED_SIZE (1)' in
        data
    ):
        data = data.replace(
            '#define MICROPY_MALLOC_USES_ALLOCATED_SIZE (1)',
            '#define MICROPY_MALLOC_USES_ALLOCATED_SIZE (0)'
        )

    if '#define MICROPY_MEM_STATS              (1)' in data:
        data = data.replace(
            '#define MICROPY_MEM_STATS              (1)',
            '#define MICROPY_MEM_STATS              (0)'
        )

    macros = (
        '#define MICROPY_SCHEDULER_DEPTH              (128)',
        '#define MICROPY_STACK_CHECK              (0)'
    )

    for macro in macros:
        if macro not in data:
            data += '\n\n'
            data += macro + '\n'

    write_file(MPCONFIGVARIANT_COMMON_PATH, data)


def compile(*args):  # NOQA
    update_makefile()
    update_modmachine()
    update_main()
    update_mpconfigvariant_common()
    update_input()
    update_unix_mphal()
    copy_micropy_updates(REAL_PORT)

    build_sdl(sdl_flags)

    cmd_ = compile_cmd[:]
    cmd_.extend(list(args))

    return_code, _ = spawn(cmd_)
    if return_code != 0:
        revert_files(REAL_PORT)
        sys.exit(return_code)

    scrub_build_folder()

    src = f'lib/micropython/ports/unix/build-{variant}/micropython'
    dst = f'build/lvgl_micropy_{REAL_PORT}'
    shutil.copyfile(src, dst)

    print(f'compiled binary is {os.path.abspath(os.path.split(dst)[0])}')
    print('You need to make the binary executable by running')
    print(f'"sudo chmod +x lvgl_micropy_{REAL_PORT}"')


def mpy_cross():
    _cmd = [
        'make -C lib/micropython/mpy-cross'
    ]

    res, _ = spawn(_cmd, cmpl=True)
    if res:
        sys.exit(res)
