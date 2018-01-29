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

import json
import re
import time

from API.common import console, utils, paths
from connections.sshcom import SSHConnection


class RPi2Device(object):
    '''
    Device of the Raspberry Pi 2 target.
    '''
    def __init__(self, env):
        self.os = 'linux'
        self.app = env['info']['app']
        self.workdir = env['info']['remote_path']

        data = {
            'username': env['info']['username'],
            'address': env['info']['address'],
            'timeout': env['info']['timeout']
        }

        self.channel = SSHConnection(data)

    def login(self):
        '''
        Login to the device.
        '''
        self.channel.open()

    def logout(self):
        '''
        Logout from the device.
        '''
        self.channel.close()

    def execute(self, testset, test):
        '''
        Execute the given test.
        '''
        self.login()

        # Absoulute path to the test file on the device.
        testfile = '%s/test/%s/%s' % (self.workdir, testset, test['name'])

        options = [
            '--app %s' % self.app,
            '--testfile %s' % testfile
        ]

        # Use the external tester script on Rapsberry Pi.
        command = 'python %s/tester.py ' % self.workdir
        # Run the remote test script on the device.
        stdout = self.channel.exec_command(command + ' '.join(options))

        self.logout()

        # Since the stdout is a JSON text, parse it.
        return json.loads(stdout)
