'''
Test stop vrs then start it
@author: Quarkonics
'''

import os
import sys
import threading
import time
import zstacklib.utils.linux as linux
import apibinding.inventory as inventory
import zstackwoodpecker.operations.resource_operations as res_ops
import zstackwoodpecker.operations.config_operations as con_ops
import zstackwoodpecker.operations.vm_operations as vm_ops
import zstackwoodpecker.operations.net_operations as net_ops
import zstackwoodpecker.operations.ha_operations as ha_ops
import zstackwoodpecker.operations.account_operations as acc_ops
import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib

_config_ = {
        'timeout' : 1000,
        'noparallel' : True
        }

session_uuid = None
test_stub = test_lib.lib_get_test_stub()

def test():
    global session_uuid
    session_uuid = acc_ops.login_as_admin()
    l3_1_name = os.environ.get('l3VlanNetworkName1')
    l3_1 = test_lib.lib_get_l3_by_name(l3_1_name)

    #create VRs.
    vrs = test_lib.lib_find_vr_by_l3_uuid(l3_1.uuid)
    if not vrs:
        vm = test_stub.create_vlan_vm(l3_name=l3_1_name)
        vm.destroy()
        vr1 = test_lib.lib_find_vr_by_l3_uuid(l3_1.uuid)[0]
    else:
        vr1 = vrs[0]

    vm_ops.destroy_vm(vr1.uuid)
    vm = test_stub.create_vlan_vm(l3_name=l3_1_name)
    vm.destroy()

    test_util.test_pass('destroy VR VM success')

def error_cleanup():
    global session_uuid
    acc_ops.logout(session_uuid)
