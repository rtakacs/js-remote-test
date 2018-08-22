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

import time

from jstest.common import utils
from jstest.testrunner import utils as testrunner_utils
from jstest.testrunner.devices.serial_device import SerialDevice

class STM32F4Device(SerialDevice):
    '''
    Device of the STM32F4-Discovery target.
    '''
    def __init__(self, env):
        self.stlink = env['modules']['stlink']

        SerialDevice.__init__(self, env, 'nuttx', 'nsh> ')

    def initialize(self):
        '''
        Flash the device.
        '''
        if not self.env.flash_enabled:
            return

        stlink = self.env['modules']['stlink']
        nuttx = self.env['modules']['nuttx']

        flash_flags = ['write', nuttx['paths']['image'], '0x8000000']

        utils.execute(stlink['src'], 'build/Release/st-flash', flash_flags)

    def reset(self):
        '''
        Reset the device to create clean environment.
        '''
        if self.env['info']['emulate']:
            return

        flasher = self.stlink['paths']['st-flash']

        utils.execute('.', flasher, ['reset'], quiet=True)
        # Wait a moment to boot the device.
        time.sleep(5)

    def execute(self, testset, test):
        '''
        Execute the given test.
        '''
        self.reset()
        self.login()

        command = self._prepare_command(testset, test)
        # Run the test on the device.
        output = self.channel.exec_command(command[self.app])

        stdout, memstat, _ = testrunner_utils.process_output(output)
        # Process the exitcode of the last command.
        exitcode = self.channel.exec_command('echo $?')

        self.logout()

        return {
            'output': stdout.rstrip('\n').replace('\n', '<br>'),
            'memstat': memstat,
            'exitcode': exitcode
        }
