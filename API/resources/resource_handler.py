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

from API.builder import targets
from API.common import paths
from API.common import utils


def load_testing_environment(options):
    '''
    Create a testing environment object that contains the
    module information and the user specified options.
    '''
    resources = utils.read_json_file(paths.RESOURCES_JSON)

    # Get the dependencies of the current device.
    deps = resources['targets'][options.device]
    # Update the deps list with user selected projects.
    deps.append(options.app)

    if options.public:
        deps.append('%s-test-results' % options.app)

    # Get the required module information.
    modules = {
        name: resources['modules'][name] for name in deps
    }

    # Update the path of the target application.
    if options.app_path:
        modules[options.app]['src'] = options.app_path
    # Add an 'app' named module that is just a reference
    # to the user defined target application.
    modules['app'] = modules[options.app]
    modules['app']['name'] = options.app

    # Create the testing environment object.
    environment = {
        'info': vars(options),
        'modules': modules,
        'paths': resources['paths']
    }

    utils.resolve_symbols(environment)

    return environment


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
            # Do not configure if the contents of deps
            # are not in the modules list.
            deps = config.get('deps', [])

            device = env['info']['device']
            # Note: Always configure in case of empty deps list.
            if deps and not any(i in modules.keys() + [device] for i in deps):
                continue

            utils.copy(config['src'], config['dst'])


def patch_modules(env, revert=False):
    '''
    Modify the source code of the required modules.
    '''
    modules = env['modules']

    for module in modules.values():
        for patch in module.get('patches', []):
            # Do not patch if target device is not
            # in the content of deps.
            deps = patch.get('deps', [])
            device = env['info']['device']

            # Note: Always configure in case of empty deps list.
            if deps and not any(i in modules.keys() + [device] for i in deps):
                continue

            if revert and not patch.get('revert', True):
                return

            # Patch the module if no submodule provided.
            project = patch.get('submodule', module['src'])
            utils.patch(project, patch['file'], revert)


def create_profile_binaries(env, target):
    '''
    Create profile builds for binary size measurement.
    '''
    if env['info']['no_profile_build']:
        return

    target.build_target(env, 'minimal', env['paths']['build-minimal'])
    target.build_target(env, 'target', env['paths']['build-target'])


def create_test_binary(env, target):
    '''
    Create the main build that is used for testing.
    '''
    build_path = env['paths']['build']
    test_files = env['paths']['build-test']

    app = env['modules']['app']
    # Copy all the tests into the build folder.
    utils.copy(app['paths']['tests'], test_files)

    target.append_files(env)
    target.build_target(env, 'target', build_path, use_extra_flags=True)


def build_deps(env, target):
    '''
    Steps for building all the necessary modules.
    '''
    if env['info']['no_build']:
        return

    fetch_modules(env)

    config_modules(env)

    create_profile_binaries(env, target)

    patch_modules(env)

    create_test_binary(env, target)

    patch_modules(env, revert=True)

    # Save binary sizes and repository info.
    utils.create_build_info(env)


def flash_device(env, target):
    '''
    Flash the appropriate device.
    '''
    if env['info']['no_flash']:
        return

    target.flash_device(env)


def initialize(env):
    '''
    Initialize the testing environment.
    '''
    target = targets.create(env)

    build_deps(env, target)
    flash_device(env, target)
