import os
import sys
from argparse import ArgumentParser
from . import spawn
from . import generate_manifest
from . import update_mphalport


board_variant = None


def parse_args(extra_args, lv_cflags, board):
    global board_variant

    if board == 'WEACTSTUDIO':
        rp2_argParser = ArgumentParser(prefix_chars='-B')

        rp2_argParser.add_argument(
            'BOARD_VARIANT',
            dest='board_variant',
            default='',
            action='store'
        )
        rp2_args, extra_args = rp2_argParser.parse_known_args(extra_args)

        board_variant = rp2_args.board_variant

    else:
        for arg in extra_args:
            if arg.startswith('BOARD_VARIANT'):
                raise RuntimeError(f'BOARD_VARIANT not supported by "{board}"')

    return extra_args, lv_cflags, board


mpy_cross_cmd = ['make', '-C', 'lib/micropython/mpy-cross']
rp2_cmd = [
    'make',
    '',
    f'-j {os.cpu_count()}',
    '-C',
    'lib/micropython/ports/rp2',
    'LV_PORT=rp2',
    'USER_C_MODULES=../../../../micropython.cmake'
]

clean_cmd = []
compile_cmd = []
submodules_cmd = []


def build_commands(_, extra_args, __, lv_cflags, board):
    rp2_cmd.extend(extra_args)

    if lv_cflags is not None:
        rp2_cmd.insert(6, f'LV_CFLAGS="{lv_cflags}"')

    if board is not None:
        if lv_cflags is not None:
            rp2_cmd.insert(7, f'BOARD={board}')
            if board_variant:
                rp2_cmd.insert(8, f'BOARD_VARIANT={board_variant}')
        else:
            rp2_cmd.insert(6, f'BOARD={board}')
            if board_variant:
                rp2_cmd.insert(7, f'BOARD_VARIANT={board_variant}')

    clean_cmd.extend(rp2_cmd[:])
    clean_cmd[1] = 'clean'

    compile_cmd.extend(rp2_cmd[:])
    compile_cmd.pop(1)

    submodules_cmd.extend(rp2_cmd[:])
    submodules_cmd[1] = 'submodules'


def build_manifest(target, script_dir, displays, indevs, frozen_manifest):
    update_mphalport(target)
    
    manifest_path = 'lib/micropython/ports/rp2/boards/manifest.py'

    generate_manifest(script_dir, manifest_path, displays, indevs, frozen_manifest)


def clean():
    spawn(clean_cmd)


def submodules():
    if 'PICO_SDK_PATH' not in os.environ:
        pico_dsk_path = os.path.abspath('lib/micropython/lib/pico-sdk')

        if not os.path.exists(
            os.path.join(pico_dsk_path, 'pico_sdk_init.cmake')
        ):
            ret_code, _ = spawn([
                ['cd', pico_dsk_path],
                ['git', 'submodule', 'update', '--init']
            ])

            if ret_code != 0:
                sys.exit(ret_code)

    return_code, _ = spawn(submodules_cmd)
    if return_code != 0:
        sys.exit(return_code)


def compile():  # NOQA
    if 'PICO_SDK_PATH' not in os.environ:
        os.environ['PICO_SDK_PATH'] = f'{os.getcwd()}/lib/micropython/lib/pico-sdk'

    return_code, _ = spawn(compile_cmd, cmpl=True)
    if return_code != 0:
        sys.exit(return_code)


def mpy_cross():
    return_code, _ = spawn(mpy_cross_cmd)
    if return_code != 0:
        sys.exit(return_code)
