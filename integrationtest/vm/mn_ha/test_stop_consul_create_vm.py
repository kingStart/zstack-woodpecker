'''

Integration Test for creating KVM VM in MN HA mode after stopping consul on MN VM running host.

@author: Mirabel
'''

import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_state as test_state
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.operations.node_operations as node_ops
import zstackwoodpecker.zstack_test.zstack_test_vm as test_vm_header
import test_stub
import time
import os

vm = None
mn_host = None

def test():
    global vm
    global mn_host
    mn_host = test_stub.get_host_by_mn_vm(test_lib.all_scenario_config, test_lib.scenario_file)
    if len(mn_host) != 1:
        test_util.test_fail('MN VM is running on %d host(s)' % len(mn_host))
    test_util.test_logger("stop consul for host [%s] that mn vm is running on" % (mn_host[0].ip_))
    test_stub.stop_consul(mn_host[0], test_lib.all_scenario_config)
    test_util.test_logger("wait for 50 seconds to see if management node VM starts on another host")
    time.sleep(50)
    try:
        new_mn_host = test_stub.get_host_by_mn_vm(test_lib.all_scenario_config, test_lib.scenario_file)
        if len(new_mn_host) == 0:
            test_util.test_fail("management node VM does not start after its former host's consul down")
        elif len(new_mn_host) > 1:
            test_util.test_fail("management node VM starts on more than one host after its former host's consul down")
    except:
        test_util.test_fail("management node VM does not start after its former host's consul down")
    test_util.test_logger("wait for 5 minutes to see if management node starts again")
    try:
        node_ops.wait_for_management_server_start(300)
    except:
        test_util.test_fail("management node does not recover after its former host's consul down")

    test_util.test_logger("try to create vm, timeout is 30s")
    time_out = 30
    while time_out > 0:
        try:
            vm = test_stub.create_basic_vm()
            break
        except:
            time.sleep(1)
            time_out -= 1
    if time_out == 0:
        test_util.test_fail('Fail to create vm after mn is ready')

    vm.check()
    vm.destroy()

    test_util.test_pass('Create VM Test Success')

#Will be called what ever test result is
def env_recover():
    test_util.test_logger("recover consul on host: %s" % (mn_host[0].ip_))
    test_stub.start_consul(mn_host[0], test_lib.all_scenario_config)

#Will be called only if exception happens in test().
def error_cleanup():
    global vm
    if vm:
        try:
            vm.destroy()
        except:
            pass
