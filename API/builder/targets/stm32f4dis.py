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

from API.builder import builder
from API.common import utils


class STM32F4Builder(builder.BuilderBase):
    '''
    Build all modules for the STM32F4-Discovery target.
    '''
    def __init__(self, options):
        super(self.__class__, self).__init__(options)

    def _build(self, profile, builddir, extra_flags=False):
        '''
        Main method to build all the dependencies of the target.
        '''
        nuttx = self.env['modules']['nuttx']

        self.prebuild_nuttx()
        self.build_application(profile, extra_flags)
        self.build_nuttx()
        self.build_stlink()

        # Copy the linker map file and the image to the build folder.
        utils.copy(nuttx['paths']['linker-map'], builddir)
        utils.copy(nuttx['paths']['image'], builddir)

    def _prebuild_nuttx(self):
        '''
        Clean NuttX and configure it for serial communication.
        '''
        nuttx = self.env['modules']['nuttx']
        config = ['stm32f4discovery/usbnsh']

        utils.execute(nuttx['paths']['tools'], './configure.sh', config)
        utils.execute(nuttx['src'], 'make', ['clean'])
        utils.execute(nuttx['src'], 'make', ['context'])

    def _build_nuttx(self):
        '''
        Build the NuttX Operating System.
        '''
        nuttx = self.env['modules']['nuttx']

        utils.define_environment('R', int(self.buildtype is 'release'))
        utils.define_environment('EXTRA_LIBS', '-Map=linker.map')

        utils.execute(nuttx['src'], 'make', ['-j1'])

    def _build_stlink(self):
        '''
        Build the ST-Link flasher tool.
        '''
        stlink = self.env['modules']['stlink']

        # Do not build if not necessary.
        if not utils.exists(stlink['paths']['st-flash']):
            return

        utils.execute(stlink['src'], 'make', ['release'])

    def _jerryscript_build_options(self, profile):
        '''
        Collect build-flags for JerryScript.
        '''
        nuttx = self.env['modules']['nuttx']
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
            '--all-in-one=ON',
            '--mem-heap=70',
            '--profile=%s' % profiles[profile],
            '--toolchain=%s' % jerry['paths']['stm32f4dis-toolchain'],
            '--compile-flag=--sysroot=%s' % nuttx['src']
        ]

        # NuttX requires the path of the used JerryScript folder.
        utils.define_environment('JERRYSCRIPT_ROOT_DIR', jerry['src'])

        return build_flags

    def _iotjs_build_options(self, profile):
        '''
        Build IoT.js for NuttX target.
        '''
        iotjs = self.env['modules']['iotjs']
        nuttx = self.env['modules']['nuttx']

        profiles = {
            'minimal': iotjs['paths']['minimal-profile'],
            'target': iotjs['paths']['nuttx-profile']
        }

        build_flags = [
            '--clean',
            '--no-parallel-build',
            '--no-init-submodule',
            '--target-arch=arm',
            '--target-os=nuttx',
            '--target-board=stm32f4dis',
            '--jerry-heaplimit=56',
            '--profile=%s' % profiles[profile],
            '--buildtype=%s' % self.buildtype,
            '--nuttx-home=%s' % nuttx['src']
        ]

        # NuttX requires the path of the used IoT.js folder.
        utils.define_environment('IOTJS_ROOT_DIR', iotjs['src'])

        return build_flags
