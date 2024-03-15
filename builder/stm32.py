import os
import sys
from . import spawn
from . import generate_manifest
from . import update_mphalport


def parse_args(extra_args, lv_cflags, board):
    return extra_args, lv_cflags, board


mpy_cross_cmd = ['make', '-C', 'lib/micropython/mpy-cross']
stm32_cmd = [
    'make',
    '',
    f'-j {os.cpu_count()}',
    '-C',
    'lib/micropython/ports/stm32',
    'LV_PORT=stm32'
]

clean_cmd = []
compile_cmd = []
submodules_cmd = []


def build_commands(_, extra_args, script_dir, lv_cflags, board):

    if lv_cflags is None:
        lv_cflags = '-DLV_USE_TINY_TTF=0'
    else:
        lv_cflags += ' -DLV_USE_TINY_TTF=0'

    stm32_cmd.append(f'USER_C_MODULES="{script_dir}/ext_mod"')

    stm32_cmd.extend(extra_args)

    if lv_cflags is not None:
        stm32_cmd.insert(6, f'LV_CFLAGS="{lv_cflags}"')

    if board is not None:
        if lv_cflags is not None:
            stm32_cmd.insert(7, f'BOARD={board}')
        else:
            stm32_cmd.insert(6, f'BOARD={board}')

    clean_cmd.extend(stm32_cmd[:])
    clean_cmd[1] = 'clean'

    compile_cmd.extend(stm32_cmd[:])
    compile_cmd.pop(1)

    submodules_cmd.extend(stm32_cmd[:])
    submodules_cmd[1] = 'submodules'


def build_manifest(target, script_dir, displays, indevs, frozen_manifest):
    update_mphalport(target)
    
    manifest_path = 'lib/micropython/ports/stm32/boards/manifest.py'

    generate_manifest(script_dir, manifest_path, displays, indevs, frozen_manifest)


def clean():
    spawn(clean_cmd)


def submodules():
    stm32lib_path = 'lib/micropython/lib/stm32lib'
    if not os.path.exists(os.path.join(stm32lib_path, 'CMSIS')):
        ret_code, _ = spawn([
            'git',
            'submodule',
            'update',
            '--init',
            '--',
            stm32lib_path
        ])

        if ret_code != 0:
            sys.exit(ret_code)

    return_code, _ = spawn(submodules_cmd)
    if return_code != 0:
        sys.exit(return_code)


def compile():  # NOQA
    return_code, _ = spawn(compile_cmd, cmpl=True)
    if return_code != 0:
        sys.exit(return_code)


def mpy_cross():
    return_code, _ = spawn(mpy_cross_cmd)
    if return_code != 0:
        sys.exit(return_code)
