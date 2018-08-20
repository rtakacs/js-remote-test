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

import binascii
import socket

from jstest.common import console, utils


def genromfs(cwd, args, env):
    '''
    Create a romfs_img from the source directory that is
    converted to a header (byte array) file. Finally, add
    a `const` modifier to the byte array to be the data
    in the Read Only Memory.
    '''
    src = args[0]
    dst = args[1]

    romfs_img = utils.join(cwd, 'romfs_img')

    utils.execute(cwd, 'genromfs', ['-f', romfs_img, '-d', src])
    utils.execute(cwd, 'xxd', ['-i', 'romfs_img', dst])
    utils.execute(cwd, 'sed', ['-i', 's/unsigned/const\ unsigned/g', dst])

    utils.remove_file(romfs_img)


def config_internet(cwd, args, env):
    '''
    Replace the Internet related symbols to concrete values in the NuttX config file.
    '''
    # IP is not provided, so the symbol is not resolved. In this case there is no
    # need to execute this function because serial config file is used.
    if args[0] == '%{ip-addr}':
        return

    ip_addr = binascii.hexlify(socket.inet_aton(args[0]))
    netmask = binascii.hexlify(socket.inet_aton(args[1]))
    gateway = binascii.hexlify(socket.inet_aton(args[2]))

    utils.execute(cwd, 'sed', ['-ie', 's/YOUR_IP_ADDR/0x%s/g' % ip_addr, 'defconfig'])
    utils.execute(cwd, 'sed', ['-ie', 's/YOUR_NETMASK/0x%s/g' % netmask, 'defconfig'])
    utils.execute(cwd, 'sed', ['-ie', 's/YOUR_ROUTER_ADDR/0x%s/g' % gateway, 'defconfig'])


NATIVES = {
  'genromfs': genromfs,
  'config_internet': config_internet
}


def get(command):
    '''
    Get a pointer to the given buil-in function.
    '''
    if command not in NATIVES:
        console.fail('%s built-in function is not found.')

    return NATIVES[command]
