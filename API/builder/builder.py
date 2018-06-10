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
        self.device = env['info']['device']
        self.deps = env['info']['deps']

        # Download all the projects.
        resources.fetch_modules(self.env)
        resources.config_modules(self.env)

        resolver = SymbolResolver(env)

    def should_build(self, config):
        '''
        Check if the build is necessary.
        '''
        if config.get('build-once') == False:
            return True

        should_build = True
        # Check if the artifacts are available at the install paths.
        # If there is no install path for the artifact (e.g. stlink),
        # the default build place is checked.
        for artifact in config.get('artifacts', []):
            path = artifact.get('src')
            path = artifact.get('install', path)

            should_build = should_build and utils.exists(path)

        return not should_build


    def do_cmd(self, command):
        '''
        Run the command defined in the build.config file.
        '''
        cwd = command.get('cwd', '.')
        cmd = command.get('cmd', '')
        args = command.get('args', [])
        env = command.get('env', {})

        # Update the arguments and the env variables with
        # the values under the condition-options.
        for option in command.get('conditional-options', []):
            if not eval(option.get('condition')):
                continue

            args.extend(option.get('args', []))
            utils.merge_dicts(env, option.get('env', {}))

        utils.execute(cwd, cmd, args=args, env=env)

    def build_modules(self):
        '''
        Build all the modules.
        '''
        configs = {}

        # In the first step, just open and save all the contents
        # that the build requires.
        for name in self.env['deps']:
            filename = utils.join(paths.BUILD_CONFIG_PATH, '%s.build.config' % name)
            # nuttx-apps git repository doesn't have build config file.
            if not utils.exists(filename):
                continue

            jsondata = utils.read_json_file(filename)
            # Save the content that belongs to the appropriate device.
            config = jsondata[self.env['info']['device']]

            if self.should_build(config):
                configs[name] = config

        # Initialize all the modules.
        for config in configs.values():
            for command in config.get('init', []):
                self.do_cmd(command)

        # Build and install the modules.
        for config in configs.values():
            self.do_cmd(config.get('build'))

            for artifact in config.get('artifacts', []):
                print artifact

                if 'install' not in artifact:
                    continue

                
                utils.copy(artifact.get('src'), artifact.get('install'))


    def build():
        '''
        '''
        for config in utils.read_json_file(paths.BUILD_CONFIG_FILE):
            builddir = utils.join(self.env['paths']['build'], config.get('id', ''))
