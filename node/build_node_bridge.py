#!/usr/bin/env python

#
# Copyright (C) 2021 Signal Messenger, LLC.
# SPDX-License-Identifier: AGPL-3.0-only
#

import optparse
import sys
import subprocess
import os
import shutil
import shlex


def main(args=None):
    if args is None:
        args = sys.argv

    if sys.platform == 'win32':
        args = shlex.split(' '.join(args), posix=0)

    print("Invoked with '%s'" % (' '.join(args)))

    parser = optparse.OptionParser()
    parser.add_option('--out-dir', '-o', default=None, metavar='DIR',
                      help='specify destination dir (default build/$CONFIGURATION_NAME)')
    parser.add_option('--configuration', default='Release', metavar='C',
                      help='specify build configuration (Release or Debug)')
    parser.add_option('--os-name', default=None, metavar='OS',
                      help='specify Node OS name')
    parser.add_option('--cargo-build-dir', default='target', metavar='PATH',
                      help='specify cargo build dir (default %default)')

    (options, args) = parser.parse_args(args)

    configuration_name = options.configuration.strip('"')
    if configuration_name is None:
        print('ERROR: --configuration is required')
        return 1
    elif configuration_name not in ['Release', 'Debug']:
        print("ERROR: Unknown value for --configuration '%s'" % (configuration_name))
        return 1

    node_os_name = options.os_name
    if node_os_name is None:
        print('ERROR: --os-name is required')
        return 1
    if node_os_name.startswith('..\\'):
        node_os_name = node_os_name[3:]

    out_dir = options.out_dir.strip('"') or os.path.join('build', configuration_name)

    cmdline = ['cargo', 'build', '-p', 'libsignal-node'] + ['--release'] if configuration_name == 'Release' else []
    print("Running '%s'" % (' '.join(cmdline)))
    cargo_env = os.environ.copy()
    cargo_env['CARGO_BUILD_TARGET_DIR'] = options.cargo_build_dir
    cmd = subprocess.Popen(cmdline, env=cargo_env)
    cmd.wait()

    if cmd.returncode != 0:
        print('ERROR: cargo failed')
        return 1

    libs_in = os.path.join(options.cargo_build_dir,
                           configuration_name.lower())

    found_a_lib = False
    for lib_format in ['%s.dll', 'lib%s.so', 'lib%s.dylib']:
        src_path = os.path.join(libs_in, lib_format % 'signal_node')
        if os.access(src_path, os.R_OK):
            dst_path = os.path.join(out_dir, 'libsignal_client_%s.node' % (node_os_name))
            print("Copying %s to %s" % (src_path, dst_path))
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            shutil.copyfile(src_path, dst_path)
            found_a_lib = True
            break

    if not found_a_lib:
        print("ERROR did not find generated library")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())