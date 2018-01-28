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


def report_testset(testset):
    console.log()
    console.log('Testset: %s' % testset, console.TERMINAL_BLUE)


def report_pass(test):
    console.log('  PASS:    %s' % test, console.TERMINAL_GREEN)


def report_fail(test):
    console.log('  FAIL:    %s' % test, console.TERMINAL_RED)


def report_timeout(test):
    console.log('  TIMEOUT: %s' % test, console.TERMINAL_RED)


def report_skip(test, reason):
    skip_message = '  SKIP:    %s' % test

    if reason:
        skip_message += '   (Reason: %s)' % reason

    console.log(skip_message, console.TERMINAL_YELLOW)


def report_start():
    console.log()
    console.log('Remote testing has been started')


def report_configuration(env):
    info = env['info']

    console.log()
    console.log("Test configuration:")
    console.log("  app:                %s" % info['app'])
    console.log("  device:             %s" % info['device'])
    console.log("  timeout:            %s sec" % info['timeout'])

    if info['device'] == "rpi2":
        console.log("  address:            %s" % info['address'])
        console.log("  username:           %s" % info['username'])
        console.log("  remote workdir:     %s" % info['remote_path'])
    elif info['device'] in ["stm32f4dis", "artik053"]:
        console.log("  port:               %s" % info['port'])
        console.log("  baud:               %d" % info['baud'])


def report_final(testresults):
    results = {}

    results['pass'] = 0
    results['fail'] = 0
    results['skip'] = 0
    results['timeout'] = 0

    for test in testresults:
        results[test['result']] += 1

    console.log()
    console.log('Finished with all tests:', console.TERMINAL_BLUE)
    console.log('  PASS:    %d' % results['pass'], console.TERMINAL_GREEN)
    console.log('  FAIL:    %d' % results['fail'], console.TERMINAL_RED)
    console.log('  TIMEOUT: %d' % results['timeout'], console.TERMINAL_RED)
    console.log('  SKIP:    %d' % results['skip'], console.TERMINAL_YELLOW)
