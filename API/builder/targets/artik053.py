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

from API.common import paths, utils


class ARTIK053Builder(builder.BuilderBase):
    '''
    Build all modules for the STM32F4-Discovery target.
    '''
    def __init__(self, options):
        super(self.__class__, self).__init__(options)

    def _build(self, profile, builddir, extra_flags=False):
        '''
        Main method to build the target.
        '''
        tizenrt = env['modules']['tizenrt']

        self._prebuild_tizenrt()
        self._build_application(profile, extra_flags)
        self._build_tizenrt()

        # Copy the linker map file and the image to the build folder.
        utils.copy(tizenrt['paths']['linker-map'], builddir)
        utils.copy(tizenrt['paths']['image'], builddir)

    def _prebuild_tizenrt(self):
        '''
        Clean TizenRT and configure it for the appropriate application.
        '''
        tizenrt = self.env['modules']['tizenrt']
        config = 'artik053/%s' % self.app

        utils.execute(tizenrt['paths']['tools'], './configure.sh', [config])
        utils.execute(tizenrt['paths']['os'], 'make', ['clean'])
        utils.execute(tizenrt['paths']['os'], 'make', ['context'])

    def _build_tizenrt(self):
        '''
        Build the TizenRT operating system.
        '''
        tizenrt = self.env['modules']['tizenrt']

        utils.execute(tizenrt['paths']['os'], 'make', ['-j1'])

    def _jerryscript_build_options(self, profile):
        '''
        Collect build-flags for JerryScript.
        '''
        tizenrt = self.env['modules']['tizenrt']
        jerry = self.env['modules']['jerryscript']

        profiles = {
            'minimal': jerry['paths']['minimal-profile'],
            'target': jerry['paths']['es2015-subset-profile']
        }

        build_flags = [
            '--clean',
            '--lto=OFF',
            '--jerry-cmdline=OFF',
            '--jerry-libc=OFF',
            '--jerry-libm=ON',
            '--all-in-one=OFF',
            '--mem-heap=70',
            '--profile=%s' % profiles[profile],
            '--toolchain=%s' % jerry['paths']['artik053-toolchain'],
            '--compile-flag=--sysroot=%s' % tizenrt['paths']['os']
        ]

        # TizenRT requires the path of the used JerryScript folder.
        utils.define_environment('JERRYSCRIPT_ROOT_DIR', jerry['src'])

        return build_flags

    def _iotjs_build_options(self, profile):
        '''
        Build IoT.js for TizenRT target.
        '''
        iotjs = self.env['modules']['iotjs']

        profiles = {
            'minimal': iotjs['paths']['minimal-profile'],
            'target': iotjs['paths']['tizenrt-profile']
        }

        build_flags = [
            '--clean',
            '--no-parallel-build',
            '--no-init-submodule',
            '--target-arch=arm',
            '--target-os=tizenrt',
            '--target-board=artik05x',
            '--profile=%s' % profiles[profile],
            '--buildtype=%s' % self.buildtype,
        ]

        iotjs_build_options = ' '.join(build_flags)
        # Note: these values should be defined for TizenRT, because
        #       it will compile the IoT.js itself.
        utils.define_environment('IOTJS_BUILD_OPTION', iotjs_build_options)

        # TizenRT requires the path of the used IoT.js folder.
        utils.define_environment('IOTJS_ROOT_DIR', iotjs['src'])

        # Since TizenRT will build IoT.js, the return value is simply `None`
        # that can indicate for the system to skip building IoT.js manually.
        return None
