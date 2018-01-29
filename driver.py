#!/usr/bin/env python

# Copyright 2017-present Samsung Electronics Co., Ltd. and other contributors
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse

import API.builder

from API.resources import resource_handler
from API.test_runner import TestRunner


def parse_options():
    '''
    Parse the given options.
    '''
    parser = argparse.ArgumentParser('[J]ava[S]cript [remote] [test]runner')

    parser.add_argument('--app',
                        choices=['iotjs', 'jerryscript'], default='iotjs',
                        help='specify the target application (default: %(default)s)')

    parser.add_argument('--app-path',
                        metavar='PATH',
                        help='specify the path to the application (default: %(default)s)')

    parser.add_argument('--buildtype',
                        choices=['release', 'debug'], default='release',
                        help='specify the build type (default: %(default)s)')

    parser.add_argument('--no-build',
                        action='store_true', default=False,
                        help='do not build the projects (default: %(default)s)')

    parser.add_argument('--no-profile-build',
                        action='store_true', default=False,
                        help='do not build the different profiles (default: %(default)s)')

    parser.add_argument('--no-flash',
                        action='store_true', default=False,
                        help='do not flash the device (default: %(default)s)')

    parser.add_argument('--no-test',
                        action='store_true', default=False,
                        help='do not test the applciation (default: %(default)s)')

    parser.add_argument('--device',
                        choices=['stm32f4dis', 'rpi2', 'artik053'], default='stm32f4dis',
                        help='specify the target device (default: %(default)s)')

    parser.add_argument('--public',
                        action='store_true', default=False,
                        help='upload the test results (default: %(default)s)')

    parser.add_argument('--timeout',
                        metavar='SEC', default=180, type=int,
                        help='specify the maximum timeout (default: %(default)s sec)')

    group = parser.add_argument_group("Secure Shell communication")

    group.add_argument('--username',
                       metavar='USER', default='pi',
                       help='specify the username (default: %(default)s)')

    group.add_argument('--address',
                       metavar='IPADDR',
                       help='specify the ip address of the device')

    group.add_argument('--remote-path',
                       metavar='PATH',
                       help='specify the test folder on the device')

    group = parser.add_argument_group("Serial communication")

    group.add_argument('--port',
                       metavar='DEVICE-ID',
                       help='specify the port of the device (e.g. /dev/ttyACM0)')

    group.add_argument('--baud',
                       type=int, default=115200,
                       help='specify the baud rate (default: %(default)s)')

    return parser.parse_args()


def main():
    '''
    Main function of the remote testrunner.
    '''
    options = parse_options()

    # Get an environment object that holds all the necessary
    # information for the build and the test.
    env = resource_handler.load_testing_environment(options)
    resource_handler.fetch_modules(env)
    resource_handler.config_modules(env)

    # Initialize the testing environment by building all the
    # required modules to be ready to run tests.
    target_builder = builder.create(env)
    target_builder.create_profile_builds()
    target_builder.cteate_test_build()

    # Run all the tests.
    testrunner = TestRunner(env)
    testrunner.run()
    testrunner.save()


if __name__ == '__main__':
    main()
