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


class Options(object):
    '''
    Merge the user and the task options.
    '''
    def __init__(self, user_options, task_options):
        self.user_options = user_options
        self.task_options = task_options

    @property
    def is_patches_enabled(self):
        return self.task_options['patches']

    @property
    def is_test_build(self):
        return 'test-build' in self.task_options['id']

    @property
    def is_profile_build(self):
        return 'profile' in self.task_options['id']

    @property
    def is_minimal_profile_build(self):
        return 'minimal' in self.task_options['id']

    @property
    def is_coverage_enabled(self):
        return self.task_options['coverage'] and bool(self.user_options['info']['coverage'])

    @property
    def is_flash_disabled(self):
        return self.task_options['info']['no_flash'] or self.user_options['no_flash']

    @property
    def is_test_disabled(self):
        return self.task_options['info']['no_test'] or self.user_options['no_test']

    @property
    def is_memstat_disabled(self):
        return self.task_options['no_memstat'] or self.user_options['no_memstat']

    @property
    def is_build_disabled(self):
        no_profile_build = self.is_profile_build and self.user_options['no_profile_build']
        no_build = self.task_options['no_build'] or self.user_options['no-build']

        return no_build or no_profile_build
