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

from API.common import utils


class BuilderBase(object):
    '''
    This class holds all the common properties of the targets.
    '''
    def __init__(self, options):
        self.app = options.app
        self.device = options.device
        self.buildtype = options.buildtype

        # Get all the information about of the modules.
        self.env = resource_handler.load_environment_info(options)

    def create_profile_builds(self):
        '''
        Build IoT.js and JerryScript on different profiles.

        Note: this step is only for binary size measurement.
        '''
        info = self.env['info']

        if info['no_build'] or info['no_profile_build']:
            return

        self._build('minimal', info['build-minimal-path'])
        self._build('target', info['build-target-path'])

    def create_test_build(self):
        '''
        Build IoT.js and JerryScript on different profiles.
        '''
        info = self.env['info']

        if info['no_build']:
            return

        self._build('target', info['build-path'], extra_flags=True)

    def _build_application(self, target, extra_flags):
        '''
        Build IoT.js or JerryScript applications.
        '''
        application = self.env['modules']['app']

        build_options = {
            'iotjs': self._iotjs_build_options(target),
            'jerryscript': self._jerryscript_build_options(target)
        }

        build_flags = build_options.get(application['name'])
        # Skip the build if there are no build flags provided.
        if not build_flags:
            return
        # Append extra-flags that are defined in the resources.json file.
        if extra_flags:
            build_flags += application['extra-build-flags'][self.device]

        utils.execute(application['src'], 'tools/build.py', build_flags)
