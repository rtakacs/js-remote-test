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

import os

# Home directory path
HOME = os.path.expanduser('~')

# Root directory of the project (dirname).
ROOT_FOLDER = os.path.join(os.path.dirname(__file__), '../..')

# Root directory of the project (abs path).
PROJECT_ROOT = os.path.abspath(ROOT_FOLDER)

#
# ================================
#

API_PATH = os.path.join(PROJECT_ROOT, 'jstest')

BUILD_PATH = os.path.join(PROJECT_ROOT, 'build')

RESULT_PATH = os.path.join(PROJECT_ROOT, 'results')

TEST_JOBS = os.path.join(PROJECT_ROOT, 'jstest', 'runnable.jobs')

BUILDER_MODULES_PATH = os.path.join(PROJECT_ROOT, 'jstest', 'builder', 'modules')

#
# ================================
#

RESOURCES_PATH = os.path.join(API_PATH, 'resources')

RESOURCES_JSON = os.path.join(RESOURCES_PATH, 'resources.json')

CONFIG_PATH = os.path.join(RESOURCES_PATH, 'configs')

PATCHES_PATH = os.path.join(RESOURCES_PATH, 'patches')

FREYA_CONFIG = os.path.join(RESOURCES_PATH, 'etc', 'iotjs-freya.config')

FREYA_TESTER = os.path.join(RESOURCES_PATH, 'etc', 'tester.py')

SIMPLE_TESTER = os.path.join(RESOURCES_PATH, 'etc', 'simpletester.py')

#
# ================================
#

TESTRUNNER_PATH = os.path.join(API_PATH, 'testrunner')

#
# ================================
#

GBS_ROOT_PATH = os.path.join(HOME, 'GBS-ROOT')

GBS_ARCH_PATH = os.path.join(GBS_ROOT_PATH, 'local/BUILD-ROOTS/scratch.armv7l.0')

GBS_IOTJS_PATH = os.path.join(GBS_ARCH_PATH, 'home/abuild/rpmbuild/BUILD/iotjs-1.0.0')
