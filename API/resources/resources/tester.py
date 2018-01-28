#!/usr/bin/env python

# Copyright 2017-present Samsung Electronics Co., Ltd. and other contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import os
import re
import subprocess
import sys

# Recommended build command for IoT.js on RPi2:
#
# tools/build.py --target-board=rpi2
#                --buildtype=release
#                --jerry-cmake-param="-DFEATURE_VALGRIND_FREYA=ON"
#                --compile-flag="-g"
#                --jerry-compile-flag="-g"

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))

FREYA_BIN = os.path.join(ROOT_PATH, 'valgrind_freya', 'vg-in-place')
FREYA_LOG = os.path.join(ROOT_PATH, 'freya.log')
FREYA_CONFIG = os.path.join(ROOT_PATH, 'iotjs-freya.config')


def is_executable(fpath):
    '''
    Check whether the file is executable.
    '''
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def is_readable(fpath):
    '''
    Check whether the file is readable.
    '''
    return os.path.isfile(fpath) and os.access(fpath, os.R_OK)


def check_tools(options):
    '''
    Checking resources before testing.
    '''
    if not is_executable(FREYA_BIN):
        sys.exit('The Freya tool is not suitable for testing!')

    if not is_readable(FREYA_CONFIG):
        sys.exit('The Freya config file is not available!')

    #if not is_executable(options.app):
    #    sys.exit('The application is not suitable for testing!')

    #if not is_readable(options.testfile):
    #    sys.exit('Testfile is not readable!')

    # Remove the last Freya log file.
    if os.path.exists(FREYA_LOG):
        os.remove(FREYA_LOG)


def execute(cwd, cmd, args=[]):
    '''
    Run the given command and return its output.
    '''
    stdout = subprocess.PIPE
    stderr = subprocess.STDOUT

    process = subprocess.Popen([cmd] + args, cwd = cwd,
                               stdout=stdout, stderr=stderr)

    output = process.communicate()[0]
    exitcode = process.returncode

    return output, exitcode


def process_output(output):
    '''
    Process the output to get jerry.
    '''
    memstat = {
        'heap-jerry': 'n/a',
        'heap-system': 'n/a',
        'stack': 'n/a'
    }

    if output.find('Heap stats:') != -1:
        # Process jerry-memstat output.
        match = re.search(r'Peak allocated = (\d+) bytes', str(output))

        if match:
            memstat['heap-jerry'] = int(match.group(1))

        # Process stack usage output.
        match = re.search(r'Stack usage: (\d+)', str(output))

        if match:
            memstat['stack'] = int(match.group(1))

        # Remove memstat from the output.
        output, _ = output.split("Heap stats:", 1)
        # Make HTML friendly stdout.
        output = output.rstrip('\n').replace('\n', '<br>')

    return output, memstat


def process_freya_output():
    '''
    Process the Freya log file to get the peak memory usage.
    '''
    if not is_readable(FREYA_LOG):
        sys.exit('Missing Freya log file!')

    measurement = open(FREYA_LOG, 'r').read()

    pattern = re.compile('\[0\] Peak:.*?(\d+)b.*\nGroup: Total')
    match = pattern.search(measurement)

    if match:
        mempeak = int(match.group(1))
    else:
        mempeak = 'n/a'

    return mempeak


def run_jerry(options):
    '''
    Run JerryScript with memcheck.
    '''
    memstat = {
        'heap-jerry': 'n/a',
        'heap-system': 'n/a',
        'stack': 'n/a'
    }

    jerryscript = os.path.join(ROOT_PATH, 'jerry')
    test_folder = os.path.join(ROOT_PATH, 'test')

    output, exitcode = execute(test_folder, jerryscript, [options.testfile, '--mem-stats'])

    # Process the memstat to get the peak memory.
    match = re.search(r'Peak allocated = (\d+) bytes', str(output))

    if match:
        memstat['heap-jerry'] = match.group(1)

    output = output.rsplit("Heap stats",1)[0]

    return {
        'output': output,
        'memstat': memstat,
        'exitcode': exitcode
    }


def run_iotjs(options):
    '''
    Run IoT.js with Freya.
    '''
    iotjs = os.path.join(ROOT_PATH, 'iotjs')

    test_folder = os.path.join(ROOT_PATH, 'test')

    # 1. Run IoT.js without Freya to get its output and exit value.
    output, exitcode = execute(test_folder, iotjs, ['--memstat', options.testfile])
    stdout, memstat = process_output(output)

    # 2. Update the configuration file of Freya:
    ldd_output, _ = execute('.', 'ldd', ['--version'])
    gnu_libc_version = ldd_output.splitlines()[0].split()[-1]

    sed_options = ['--in-place', 's/YOUR_GLIBC_VERSION/%s/g' % gnu_libc_version, 'iotjs-freya.config']
    execute(ROOT_PATH, 'sed', sed_options)

    # 3. Run IoT.js with Freya to create a log file with the memory information.
    valgrind_options = [
        '--tool=freya',
        '--freya-out-file=%s' % FREYA_LOG,
        '--config=%s' % FREYA_CONFIG,
        iotjs,
        '--memstat',
        options.testfile
    ]

    execute(ROOT_PATH, FREYA_BIN, valgrind_options)

    # 4. Process the created log file to get the peak memory.
    memstat['heap-system'] = process_freya_output()

    return {
        'output': stdout,
        'memstat': memstat,
        'exitcode': exitcode
    }


def check_stack_usage(options, text):
    '''
    Run the given binary to check stack usage.
    '''
    output, _ = execute(options.cwd, options.cmd, [options.testfile])

    match = re.search(r'%s(\d+)' % text, output)

    if match:
        stack = int(match.group(1))
    else:
        stack = 'n/a'

    return { 'stack': stack }


def parse_arguments():
    '''
    Parse the given arguments.
    '''
    parser = argparse.ArgumentParser()

    parser.add_argument('--app', choices=['iotjs', 'jerryscript'],
                        help='specify the target application')

    parser.add_argument('--testfile',
                        help='specify the apth to the testfile')

    return parser.parse_args()


def main():
    '''
    Main function of the tester script.
    '''
    arguments = parse_arguments()

    check_tools(arguments)

    if arguments.app == 'iotjs':
        results = run_iotjs(arguments)

    if arguments.app == 'jerryscript':
        results = run_jerry(arguments)

    # Don't remove this print function. The result will be on the
    # SSH socket when testing remotely.
    print(json.dumps(results))


if __name__ == '__main__':
    main()
