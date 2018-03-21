# Copyright 2018-present Samsung Electronics Co., Ltd. and other contributors
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

from API.common import console, utils, paths
from connections.sshcom import SSHConnection


class ARTIK530Device(object):
    '''
    Device of the ARTIK530 target.
    '''
    def __init__(self, env):
        self.os = 'tizen'
        self.app = env['info']['app']
        self.user = env['info']['username']
        self.address = env['info']['address']
        self.workdir = env['info']['remote_workdir']
        self.env = env

        # Check the members before testing.
        self.check_args()

        data = {
            'username': self.user,
            'address': self.address,
            'timeout': env['info']['timeout'],
        }

        self.channel = SSHConnection(data)

    def check_args(self):
        '''
        Check that all the arguments are established.
        '''
        if not self.workdir:
            console.fail('Please use --remote-workdir for the device.')
        if not self.address:
            console.fail('Please define the IP address of the device.')
        if not self.user:
            console.fail('Please define the username of the device.')

        if self.workdir is '/':
            console.fail('Please do not use the root folder as test folder.')

    def initialize(self):
        '''
        Flash the device.
        '''
        if self.env['info']['no_flash']:
            return

        target_app = self.env['modules']['app']
        build_path = self.env['paths']['build']

        test_src = target_app['paths']['tests']
        test_dst = utils.join(build_path, 'test')

        # 1. Copy all the necessary files.
        # Copy applicaiton RPM package file.
        rpm_package_path = self.env['paths']['tizen-rpm-package']
        utils.copy(rpm_package_path, build_path)

        # Copy all the tests into the build folder.
        utils.copy(test_src, test_dst)
        utils.copy(paths.SIMPLE_TESTER, build_path)
        utils.copy(paths.FREYA_CONFIG, build_path)
        utils.copy(paths.FREYA_TESTER, build_path)

        # 2. Deploy the build folder to the device.
        #self.login()

        #self.channel.exec_command('mount -o remount,rw /')
        rsync_flags = ['-e', '\'ssh -p 9983\'', '--recursive', '--compress', '--delete']

        # Note: slash character is required after the path.
        # In this case `rsync` copies the whole folder, not
        # the subcontents to the destination.
        src = self.env['paths']['build'] + '/'
        dst = '%s@%s:%s' % (self.user, self.address, self.workdir)

        utils.execute('.', 'rsync', rsync_flags + [src, dst])

        # 3. Install rpm package
        self.login()
        template = 'rpm -ivh --force --nodeps %s/%s-1.0.0-0.armv7l.rpm'
        self.channel.exec_command(template % (self.workdir, self.app))

        self.logout()

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

        template = 'python3 %s/tester.py --cwd %s --cmd %s --testfile %s'
        # Absolute path to the test folder.
        testdir = '%s/test' % self.workdir
        # Absolute path to the test file.
        testfile = '%s/%s/%s' % (testdir, testset, test['name'])
        # Absolute path to the application.
        apps = {
            'iotjs': '%s/iotjs' % self.workdir,
            'jerryscript': '%s/jerry' % self.workdir
        }

        # Create the command that the device will execute.
        command = template % (self.workdir, testdir, apps[self.app], testfile)

        print command
        stdout = self.channel.exec_command(command)
        print stdout

        # Since the stdout is a JSON text, parse it.
        result = json.loads(stdout)

        # Make HTML friendly stdout.
        result['output'] = result['output'].decode('UTF-8', 'ignore').rstrip('\n').replace('\\\\n', '<br>')

        self.logout()

        return result
