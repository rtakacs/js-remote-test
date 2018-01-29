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

#from API.testrunner import targets
from API.common import reporter, utils, paths
import targets


def read_testsets(env):
    '''
    Read all the tests into dictionary.
    '''
    if env['info']['app'] == 'iotjs':
        iotjs = env['modules']['iotjs']
        testsets = utils.read_json_file(iotjs['paths']['testfiles'])

    elif env['info']['app'] == 'jerryscript':
        testsets = utils.read_test_files(env)

    return testsets


def read_skiplist(env):
    '''
    Read the local skiplists.
    '''
    app_name = env['info']['app']
    dev_name = env['info']['device']

    skiplist = {
       'iotjs': 'iotjs-skiplist.json',
       'jerryscript': 'jerryscript-skiplist.json'
    }

    skipfile = utils.join(paths.TESTRUNNER_PATH, skiplist[app_name])
    skiplist = utils.read_json_file(skipfile)

    return skiplist[dev_name]


def find_in_skiplist(testset, test, skiplist, os):
    '''
    Find element in the skiplist.
    '''
    for obj in skiplist['testsets']:
        if obj['name'] == testset:
            return obj

    for obj in skiplist['testfiles']:
        if obj['name'] == test['name']:
            return obj

    # IoT.js official skiplist.
    for i in ['all', 'stable', os]:
        if i in test.get('skip', []):
            return test

    return None


def skip_test(testset, test, skiplist, os):
    '''
    Skip tests by the skiplists.
    '''
    result = find_in_skiplist(testset, test, skiplist, os)

    if result and 'reason' in result:
        test['reason'] = result['reason']

    return bool(result)


class TestRunner(object):
    '''
    Testrunner class.
    '''
    def __init__(self, environment):
        self.env = environment

        self.device = targets.create_device(environment)
        self.local_skiplist = read_skiplist(environment)
        self.results = []

    def run(self):
        '''
        Main method to run IoT.js or JerryScript tests.
        '''
        reporter.report_configuration(self.env)

        for testset, tests in read_testsets(self.env).items():
            self.run_testset(testset, tests)

        reporter.report_final(self.results)

    def run_testset(self, testset, tests):
        '''
        Run all the tests that are in the given testset.
        '''
        reporter.report_testset(testset)

        for test in tests:
            testresult = {
                'name': test['name']
            }

            # 1. Skip tests.
            if skip_test(testset, test, self.local_skiplist, self.device.os):
                reporter.report_skip(test['name'], test.get('reason'))

                testresult['result'] = 'skip'
                testresult['reason'] = test.get('reason')
                self.results.append(testresult)

                continue

            # 2. Execute the test and handle timeout.
            try:
                result = self.device.execute(testset, test)

            except Exception:
                reporter.report_timeout(test['name'])

                testresult['result'] = 'timeout'
                self.results.append(testresult)

                continue

            print result

            # 3. Process the result of the test.
            expected_failure = test.get('expected-failure', False)
            exitcode = int(result['exitcode'])

            if bool(exitcode) == expected_failure:
                reporter.report_pass(test['name'])

                testresult['result'] = 'pass'
                testresult['memstat'] = result['memstat']

            else:
                reporter.report_fail(test['name'])
                testresult['result'] = 'fail'

            self.results.append(testresult)

    def save(self):
        '''
        Save the current testresults into JSON format.
        '''
        build_dir = utils.get_build_path(self.env)
        build_info_file = utils.join(build_dir, 'build.json')
        build_info = utils.read_json_file(build_info_file)

        # Merge the build information and the test results.
        test_info = {
            'date': build_info['last-commit-date'],
            'bin': build_info['bin'],
            'submodules': build_info['submodules'],
            'tests': self.results
        }

        # Save the results into a date named file.
        test_dir = utils.get_result_path(self.env)
        filename = utils.join(test_dir, build_info['last-commit-date'])

        utils.write_json_file(filename + '.json', test_info)

        # Publish the results if necessary.
        utils.upload_data_to_firebase(self.env, test_info)
