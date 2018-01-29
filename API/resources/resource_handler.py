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
