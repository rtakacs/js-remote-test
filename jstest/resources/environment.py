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

from jstest.common import paths, utils


class ObjectDict(dict):
    '''
    Helper class to refer dict members as object property.
    '''
    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        if name in self:
            return self[name]

        raise AttributeError("No attribute found: " + name)

    def __delattr__(self, name):
        if name in self:
            del self[name]

        raise AttributeError("No attribute found: " + name)


def decode_as_objdict(value):
    '''
    Converts dictionaries to ObjectDict.
    '''
    if isinstance(value, dict):
        return ObjectDict(value)

    return value


class Environment(object):
    '''
    Testing environment.
    '''
    def __init__(self, options, default_options):
        self.default_options = default_options
        # This dictionary will be reachable as an object.
        #self.__dict__ = self.load_module_info(options)
        self.modules = self.load_module_info(options)

        # FIXME: find a better mode to resolve the symbols. Maybe
        # the resources.json could be separated.
        resolved = utils.resolve_symbols(json.dumps(self.modules), self)

        self.modules = json.loads(resolved)

    def __getitem__(self, name):
        return self.modules[name]

    def __setitem__(self, name, value):
        self.modules[name] = value

    def load_module_info(self, options):
        '''
        Load the resource infromation that all modules define.
        '''
        resources = utils.read_json_file(paths.RESOURCES_JSON, decoder=decode_as_objdict)

        # Get the dependencies of the current device.
        deps = resources['targets'][options.device]
        # Update the deps list with user selected project.
        deps.insert(0, options.app)

        # Get the required module information. Drop all the
        # modules that are not required by the target.
        modules = {
            name: resources['modules'][name] for name in deps
        }

        # Update the path of the target application if custom
        # iotjs or jerryscript is used.
        if options.app_path:
            modules[options.app]['src'] = options.app_path
        # Add an 'app' named module that is just a reference
        # to the user defined target application.
        modules['app'] = modules[options.app]
        modules['app']['name'] = options.app

        environment = {
            'info': vars(options),
            'modules': modules,
            'paths': resources['paths']
        }

        return environment

    @property
    def patch_enabled(self):
        '''
        Check if project modifications are enabled or disabled.
        '''
        return self.default_options['patches']

    @property
    def test_build(self):
        '''
        Check if the job is minimal profile or not.
        '''
        return 'test' in self.default_options['id']

    @property
    def profile_build(self):
        '''
        Check if the job is profile or not.
        '''
        return 'profile' in self.default_options['id']

    @property
    def minimal_profile_build(self):
        '''
        Check if the job is minimal profile or not.
        '''
        return 'minimal' in self.default_options['id']

    @property
    def build_directory(self):
        '''
        Return the build directory for the current job.
        '''
        return utils.join(self.modules['paths']['build'], self.default_options['id'])

    @property
    def build_enabled(self):
        '''
        Check if build is enabled or disabled.
        '''
        info = self.modules['info']

        no_profile_build = self.profile_build and info['no_profile_build']

        return not (info['no_build'] or self.default_options['no_build'] or no_profile_build)

    @property
    def flash_enabled(self):
        '''
        Check if flash is enabled or disables.
        '''
        return not (self.modules['info']['no_flash'] or self.default_options['no_flash'])

    @property
    def test_enabled(self):
        '''
        Check if test is enabled or disables.
        '''
        return not (self.modules['info']['no_test'] or self.default_options['no_test'])

    @property
    def memstat_enabled(self):
        '''
        Check if memstat is enabled or disables.
        '''
        return not (self.modules['info']['no_memstat'] or self.default_options['no_memstat'])

    @property
    def coverage_enabled(self):
        '''
        Check if coverage is enabled or disables.
        '''
        if self.modules['info']['app'] == 'jerryscript':
            return False

        return bool(self.modules['info']['coverage']) and self.default_options['coverage']
