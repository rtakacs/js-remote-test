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

import re
import time

from API.common import console, utils, paths
from connections.serialcom import SerialConnection


def process_output(output):
    '''
    Extract the runtiome memory information from the output of the test.
    '''
    memstat = {
        'heap-jerry': 'n/a',
        'heap-system': 'n/a',
        'stack': 'n/a'
    }

    if output.find('Heap stats:') != -1:
        # Process jerry-memstat output.
        match = re.search(r'Peak allocated = (\d+) bytes', output)

        if match:
            memstat['heap-jerry'] = match.group(1)

        # Process malloc peak output.
        match = re.search(r'Malloc peak allocated: (\d+) bytes', output)

        if match:
            memstat['heap-system'] = match.group(1)

        # Process stack usage output.
        match = re.search(r'Stack usage: (\d+)', output)

        if match:
            memstat['stack'] = match.group(1)

        # Remove memstat from the output.
        output, _ = output.split('Heap stats:', 1)
        # Make HTML friendly stdout.
        output = output.rstrip('\n').replace('\n', '<br>')

    return output, memstat


class STM32F4Device(object):
    '''
    Device of the STM32F4-Discovery target.
    '''
    def __init__(self, env):
        self.os = 'nuttx'
        self.app = env['info']['app']
        self.stlink = env['modules']['stlink']

        data = {
            'port': env['info']['port'],
            'baud': env['info']['baud'],
            'timeout': env['info']['timeout'],
            'prompt': 'nsh> '
        }

        self.channel = SerialConnection(data)

    def reset(self):
        '''
        Reset the device to create clean environment.
        '''
        flasher = self.stlink['paths']['st-flash']

        utils.execute('.', flasher, ['reset'], quiet=True)
        # Wait a moment to boot the device.
        time.sleep(5)

    def login(self):
        '''
        Login to the device.
        '''
        try:
            self.channel.open()

            # Press enters to start the serial communication and
            # go to the test folder because some tests require resources.
            self.channel.exec_command('\n\n')
            self.channel.exec_command('cd /test')

        except Exception as e:
            console.fail(str(e))

    def logout(self):
        '''
        Logout from the device.
        '''
        self.channel.close()
 
    def execute(self, testset, test):
        '''
        Execute the given test.
        '''
        self.reset()
        self.login()

        # Absoulute path to the test file on the device.
        testfile = '/test/%s/%s' % (testset, test['name'])

        command = {
            'iotjs': 'iotjs --memstat %s' % testfile,
            'jerryscript': 'jerry %s --mem-stats' % testfile
        }

        # Run the test on the device.
        stdout = self.channel.exec_command(command[self.app])

        stdout, memstat = process_output(stdout)
        # Process the exitcode of the last command.
        exitcode = self.channel.exec_command('echo $?')

        self.logout()

        return {
            'output': stdout,
            'memstat': memstat,
            'exitcode': exitcode
        }
