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

import console
import json
import lumpy
import os
import paths
import platform
import re
import shutil
import subprocess
import time
import paths
import pyrebase


class TimeoutException(Exception):
    '''
    Custom exception in case of timeout.
    '''
    pass


def execute(cwd, cmd, args=[], quiet=False):
    '''
    Run the given command.
    '''
    stdout = None
    stderr = None

    console.info(cmd + ' ' + ' '.join(args))

    if quiet:
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT

    try:
        process = subprocess.Popen([cmd] + args, stdout=stdout,
                                   stderr=stderr, cwd=cwd)

        output = process.communicate()[0]
        exitcode = process.returncode
        if exitcode:
            raise Exception('Not null exit value')

        if quiet:
            output = re.sub(' +', ' ', output)
            output = re.sub('\n\n', '\n', output)
            output = re.sub('\n ', '\n', output)

        return output, exitcode

    except Exception as e:
        console.fail('[Failed - %s] %s' % (cmd, str(e)))


def patch(project, patch, revert=False):
    '''
    Apply the given patch to the given project.
    '''
    patch_cmd = ['patch', '-p1', '-d', project]
    dry_options = ['--dry-run', '-R', '-f', '-s', '-i']

    if not os.path.exists(patch):
        console.fail(patch + ' does not exist.')

    # First check if the patch can be applied to the project.
    patch_applicable = subprocess.call(patch_cmd + dry_options + [patch])

    # Apply the patch if project is clean and revert flag is not set.
    if not revert and patch_applicable:
        if subprocess.call(patch_cmd + ['-i', patch]):
            console.fail('Failed to apply ' + patch)

    # Revert the patch if the project already contains the modifications.
    if revert and not patch_applicable:
        if subprocess.call(patch_cmd + ['-i', patch, '-R']):
            console.fail('Failed to revert ' + patch)

def generate_romfs(src, dst):
    '''
    Create a romfs_img from the source directory that is
    converted to a header (byte array) file. Finally, add
    a `const` modifier to the byte array to be the data
    in the Read Only Memory.
    '''
    romfs_img = join(paths.BUILD_PATH, 'romfs_img')

    execute(paths.BUILD_PATH, 'genromfs', ['-f', romfs_img, '-d', src])
    execute(paths.BUILD_PATH, 'xxd', ['-i', 'romfs_img', dst])
    execute(paths.BUILD_PATH, 'sed', ['-ie', 's/unsigned/const\ unsigned/g', dst])

    os.remove(romfs_img)


def write_json_file(filename, data):
    '''
    Write a JSON file from the given data.
    '''
    mkdir(dirname(filename))

    with open(filename, 'w') as filename_p:
        json.dump(data, filename_p, indent=2)

        # Add a newline to the end of the line.
        filename_p.write('\n')


def read_json_file(filename):
    '''
    Read JSON file.
    '''
    with open(filename, 'r') as file:
        return json.load(file)


def read_file(filename):
    '''
    Read a simple text file.
    '''
    with open(filename, 'r') as file:
        return file.read()


def copy(src, dst):
    '''
    Copy src to dst.
    '''
    if os.path.isdir(src):
        # Remove dst folder because copytree function
        # fails when is already exists.
        if exists(dst):
            shutil.rmtree(dst)

        shutil.copytree(src, dst, symlinks=False, ignore=None)

    else:
        # Create dst if it does not exist.
        if not exists(dst):
            os.makedirs(dst)
        shutil.copy(src, dst)


def move(src, dst):
    '''
    Move a file or directory to another location.
    '''
    shutil.move(src, dst)


def make_archive(folder, fmt):
    '''
    Create an archive file (eg. zip or tar)
    '''
    return shutil.make_archive(folder, fmt, folder)


def mkdir(directory):
    '''
    Create directory.
    '''
    if exists(directory):
        return

    os.makedirs(directory)


def define_environment(env, value):
    '''
    Define environment.
    '''
    os.environ[env] = value


def get_environment(env):
    '''
    Get environment value.
    '''
    return os.environ.get(env)


def unset_environment(env):
    '''
    Unset environment.
    '''
    os.unsetenv(env)


def exists(path):
    '''
    Checks that the given path is exist.
    '''
    return os.path.exists(path)


def size(binary):
    '''
    Get the size of the given program.
    '''
    return os.path.getsize(binary)


def join(path, *paths):
    '''
    Join one or more path components intelligently.
    '''
    return os.path.join(path, *paths)


def dirname(file):
    '''
    Return the folder name.
    '''
    return os.path.dirname(file)


def basename(path):
    '''
    Return the base name of pathname path.
    '''
    return os.path.basename(path)


def abspath(path):
    '''
    Return the absolute path.
    '''
    return os.path.abspath(path)


def relpath(path, start):
    '''
    Return a relative filepath to path from the start directory.
    '''
    return os.path.relpath(path, start)


def rmtree(path):
    '''
    Remove directory
    '''
    if exists(path):
        shutil.rmtree(path)


def get_section_sizes_from_map(mapfile):
    '''
    Returns the sizes of the main sections.
    '''
    sizes = {
        'bss': 0,
        'text': 0,
        'data': 0,
        'rodata': 0,
        'total': 0
    }

    if not exists(mapfile):
        return sizes

    archives = [
        'libhttpparser.a',
        'libiotjs.a',
        'libjerry-core.a',
        'libjerry-ext.a',
        'libjerry-port-default.a',
        'libjerry-port-default-minimal.a',
        'libtuv.a'
    ]

    data = lumpy.load_map_data(mapfile)

    sections = lumpy.parse_to_sections(data)
    # Extract .rodata section from the .text section.
    lumpy.hoist_section(sections, ".text", ".rodata")

    for s in sections:
        for section_key in sizes:
            if s['name'] == '.%s' % section_key:
                for ss in s['contents']:
                    if ss['path'].endswith('.c.obj)') or \
                        len(filter(lambda ar: '/%s(' % ar in ss['path'], archives)):
                        sizes[section_key] += ss['size']
                break

    sizes['total'] = sizes['text'] + sizes['data'] + sizes['rodata']
    return sizes


def get_section_sizes(executable):
    '''
    Returns the sizes of the main sections.
    '''

    args = ['-A', executable]
    sections, _ = execute(os.curdir, 'arm-linux-gnueabi-size', args, quiet=True)

    sizes = {}
    for line in sections.splitlines():
        for key in ['text', 'data', 'rodata', 'bss']:
            if '.%s' % key in line:
                sizes[key] = line.split()[1]

    sizes['total'] = size(executable)

    return sizes


def get_app_module(env):
    '''
    Get the application module.
    '''
    app_name = env['info']['app']

    return env['modules'][app_name]


def get_result_path(env):
    '''
    Get result path using the environemnt information.
    '''
    info = env['info']

    return join(paths.OUTPUT_PATH, '%s/%s' % (info['app'],
                                              info['device']))


def get_build_path(env):
    '''
    Get build path using the environemnt information.
    '''
    info = env['info']

    return join(paths.BUILD_PATH, info['app'], info['device'], info['buildtype'])


def get_test_path(env):
    '''
    Get test path using the environemnt information.
    '''
    return join(get_build_path(env), 'test')


def get_profile_path(env, profile):
    '''
    Get profile build path using the environemnt information.
    '''
    return join(get_build_path(env), 'profiles', profile)


def get_extra_build_flags(env):
    '''
    Get extra build flags using the environemnt information.
    '''
    app_name = env['info']['app']
    dev_name = env['info']['device']
    modules = env['modules']

    return modules[app_name]['extra-build-flags'][dev_name]


def get_remote_path(env):
    '''
    Get the remote path of the target device.
    '''
    info = env['info']

    return '{user}@{ip}:{path}'.format(user=info['username'],
                                       ip=info['address'],
                                       path=info['remote_path'])


def last_commit_info(git_repo_path):
    '''
    Get last commit information about the submodules.
    '''
    info = {
        'message': None,
        'commit': None,
        'author': None,
        'date': None
    }

    # Linux repository isn't exist.
    if git_repo_path == 'linux':
        return info

    git_flags = [
        'log',
        '-1',
        '--date=format-local:%Y-%m-%dT%H:%M:%SZ',
        '--format=%H%n%an <%ae>%n%cd%n%s'
    ]

    output, status_code = execute(git_repo_path, 'git', git_flags, quiet=True)
    output = output.splitlines()

    info['commit'] = output[0] if status_code == 0 else 'n/a'
    info['author'] = output[1] if status_code == 0 else 'n/a'
    info['date'] = output[2] if status_code == 0 else 'n/a'
    info['message'] = output[3] if status_code == 0 else 'n/a'

    return info


def create_build_info(env):
    '''
    Write binary size and commit information into a file.
    '''
    app_name = env['info']['app']
    build_path = get_build_path(env)

    # Binary size information.
    minimal_map = join(build_path, 'profiles', 'minimal', 'linker.map')
    target_map = join(build_path, 'profiles', 'target', 'linker.map')

    bin_sizes = {
        'minimal-profile': get_section_sizes_from_map(minimal_map),
        'target-profile': get_section_sizes_from_map(target_map)
    }

    # Git commit information from the projects.
    submodules = {}

    for name, module in env['modules'].iteritems():
        submodules[name] = last_commit_info(module['src'])

    # Merge the collected values into a result object.
    build_info = {
        'build-date': get_standardized_date(),
        'last-commit-date': submodules[app_name]['date'],
        'bin': bin_sizes,
        'submodules': submodules
    }

    write_json_file(join(build_path, 'build.json'), build_info)


def upload_data_to_firebase(env, test_info):
    '''
    Upload the results of the testrunner to the Firebase database.
    '''
    info = env['info']

    if not info['public']:
        return

    email = get_environment('FIREBASE_USER')
    password = get_environment('FIREBASE_PWD')

    if not (email and password):
        return

    config = {
        'apiKey': 'AIzaSyDMgyPr0V49Rdf5ODAU9nLY02ZGEUNoxiM',
        'authDomain': 'remote-testrunner.firebaseapp.com',
        'databaseURL': 'https://remote-testrunner.firebaseio.com',
        'storageBucket': 'remote-testrunner.appspot.com',
    }

    firebase = pyrebase.initialize_app(config)
    database = firebase.database()
    authentication = firebase.auth()

    # Identify the place where the data should be stored.
    database_path = '%s/%s' % (info['app'], info['device'])

    user = authentication.sign_in_with_email_and_password(email, password)
    #database.child(database_path).push(test_info, user['idToken'])


def to_int(value):
    '''
    Return the value as integer type.
    '''
    if isinstance(value, int):
        return value

    return 0


def get_standardized_date():
    '''
    Get the current date in standardized format.
    '''
    return time.strftime('%Y-%m-%dT%H.%M.%SZ')


def get_system():
    '''
    Get the underlying platform name.
    '''
    return platform.system()


def get_architecture():
    '''
    Get the architecture on platform.
    '''
    return platform.architecture()[0][:2]


def resolve_symbols(env):
    '''
    Resolve all the symbols in the environment object.

    "%%src/test/" -> /home/user/iotjs/test/
    '''
    for key, value in env.iteritems():
        env[key] = resolve(value, env)


def resolve(node, env):
    '''
    Recursive function to loop the environment object
    and replace the symbols.
    '''
    if not isinstance(node, dict):
        return node

    for key, value in node.iteritems():
        if isinstance(value, dict):
            node[key] = resolve(value, env)
        elif isinstance(value, list):
            ret = []
            for obj in value:
                ret.append(resolve(obj, env))
            node[key] = ret
        elif isinstance(value, str) or isinstance(value, unicode):
            node[key] = replacer(value, env)

    return node


def replacer(string, env):
    '''
    Replace symbols with the corresponding string data.
    '''
    if not '%' in string:
        return string

    # These symbols always could be resolved.
    symbol_mapping = {
        '%app': env['info']['app'],
        '%device': env['info']['device'],
        '%build-type': env['info']['buildtype'],
        '%js-remote-test': paths.PROJECT_ROOT,
        '%build-path': paths.BUILD_PATH,
        '%patches': paths.PATCHES_PATH,
        '%config': paths.CONFIG_PATH,
    }

    for symbol, value in symbol_mapping.items():
        string = string.replace(symbol, value)

    modules = env['modules']
    # Process the remaining symbols that are
    # reference to other modules.
    symbols = re.findall(r'%(.*?)/', string)

    for name in symbols:
        # Skip if the module does not exist.
        if name not in modules:
            continue

        string = string.replace('%' + name, modules[name]['src'])

    return string


def read_test_files(env):
    '''
    Read all the tests from the given folder and create a
    dictionary similar to the IoT.js testsets.json file.
    '''
    testsets = {}
    # Read all the tests from the build folder.
    testpath = join(get_build_path(env), 'test')

    for root, dirs, files in os.walk(testpath):
        # The name of the testset is always the folder name.
        testset = relpath(root, testpath)

        # Create a new testset entry if it doesn't exist.
        if not testset in testsets:
            testsets[testset] = []

        for filename in files:
            test = {
                'name': filename
            }

            if 'fail' in testset:
                test['expected-failure'] = True

            testsets[testset].append(test)

    return testsets