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

from API import resources
from API.common import utils, paths


class BuilderBase(object):
    '''
    This class holds all the common properties of the targets.
    '''
    def __init__(self, env):
        # Get all the information about of the modules.
        self.env = env

        # Download all the projects.
        resources.fetch_modules(self.env)
        resources.config_modules(self.env)

    def build(self, command):
        '''
        '''
        cwd = command.get('cwd', '.')
        cmd = command.get('cmd')
        args = command.get('args', [])
        env = command.get('env', {})

        # Get the conditional options and appens their data to
        # the appropriate place.
        for i in command.get('conditional-options', []):
            if eval(i.get('condition')):
                args.extend(i.get('args', []))
                utils.merge_dicts(env, i.get('env', {}))

        utils.execute(cwd, cmd, args=args, env=env)

    def build_modules(self):
        '''
        Build all the modules.
        '''
        configs = {}

        # In the first step, just open and save all the contents
        # that the build requires.
        for name in self.env['deps']:
            print name
            filename = utils.join(paths.BUILDER_PATH, '%s.build.config' % name)
            jsondata = utils.read_json_file(filename)
            # Save the content that belongs to the appropriate device.
            commands = jsondata[self.env['info']['device']]
            configs[name] = commands

            # Initialize all the modules.
            for command in commands.get('init', []):
                self.build(command)

        # Loop on the saved build configurations and build the modules.
        for config in configs.values():
            print config
            self.build(config.get('build'))

            # Install the components.
            for command in config.get('install', []):
                self.build(command)
