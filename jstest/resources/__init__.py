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

from jstest.common import paths, utils


def fetch_modules(env):
    '''
    Download all the required modules.
    '''
    modules = env['modules']

    for module in modules.values():
        # Skip if the module is already exist.
        if utils.exists(module['src']):
            continue

        fetch_url = module['url']
        fetch_dir = module['src']

        utils.execute('.', 'git', ['clone', fetch_url, fetch_dir])
        utils.execute(module['src'], 'git', ['checkout', module['version']])
        utils.execute(module['src'], 'git', ['submodule', 'update', '--init'])


def config_modules(env):
    '''
    Configure all the required modules.
    '''
    modules = env['modules']

    for module in modules.values():
        for config in module.get('config', []):
            # Do not configure if the result of the condition is false.
            condition = config.get('condition', 'True')

            if not eval(condition):
                continue

            utils.symlink(config['src'], config['dst'])


def patch_modules(env, revert=False):
    '''
    Modify the source code of the required modules.
    '''
    if not env.patch_enabled:
        return

    modules = env['modules']

    for module in modules.values():
        for patch in module.get('patches', []):
            # Do not patch if the result of the condition is false.
            condition = patch.get('condition', 'True')

            if not eval(condition):
                continue

            revertable = patch.get('revert', True)
            # Note: some patches should not be removed
            # because sometimes the testing requires the
            # modifications.
            if revert and not revertable:
                continue

            # By default, the project is patched. If there is a
            # submodule information, the subproject will be patched.
            project = patch.get('submodule', module['src'])
            utils.patch(project, patch['file'], revert)
