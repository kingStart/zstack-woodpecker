'''

@author: SyZhao
'''
import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.test_state as test_state
import zstackwoodpecker.operations.resource_operations as res_ops
import zstacklib.utils.ssh as ssh
import os


test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()



def exec_cmd_in_vm(vm, cmd, fail_msg):
    ret, output, stderr = ssh.execute(cmd, vm.get_vm().vmNics[0].ip, "root", "password", False, 22)
    if ret != 0:
        test_util.test_fail(fail_msg)


def ensure_storage_online(vm):
    ret, output, stderr = ssh.execute("o2cb.init status", vm.get_vm().vmNics[0].ip, "root", "password", False, 22)
    if ret != 0:
        test_util.test_fail( cmd + " failed")

    if "online" not in output.lower():
        test_util.test_fail("not found storage online")
     

def mkfs_sharable_volume(vm):
    """
    This function only can be invoked after sharable volume has already successfully attached.
    Notice this fuction is just need to execute once although there are 2 hosts in the cluster.
    """

    cmd = r"mkfs.ocfs2 --cluster-stack=o2cb -C 256K -J size=8M -N 16 -L ocfs2-disk1 --cluster-name=zstackstorage --fs-feature-level=default -T vmstore /dev/sda"
    exec_cmd_in_vm(vm, cmd, "sharable volume mkfs failed")



def config_ocfs2_vms(vm1, vm2):
    """
    This function configure the ocfs2 host machine
    """
    cmd = "sed -i \"s:\([0-9]\{1,3\}\.\)\{3\}[0-9]\{1,3\}   ocfs2-host1:" + vm1.get_vm().vmNics[0].ip + "   ocfs2-host1:g\" /etc/hosts"
    exec_cmd_in_vm(vm1, cmd, "change vm1 hostname&ip1 failed")

    cmd = "sed -i \"s:\([0-9]\{1,3\}\.\)\{3\}[0-9]\{1,3\}   ocfs2-host2:" + vm2.get_vm().vmNics[0].ip + "   ocfs2-host2:g\" /etc/hosts"
    exec_cmd_in_vm(vm1, cmd, "change vm1 hostname&ip2 failed")

    cmd = "sed -i \"s:\([0-9]\{1,3\}\.\)\{3\}[0-9]\{1,3\}   ocfs2-host1:" + vm1.get_vm().vmNics[0].ip + "   ocfs2-host1:g\" /etc/hosts"
    exec_cmd_in_vm(vm2, cmd, "change vm2 hostname&ip1 failed")

    cmd = "sed -i \"s:\([0-9]\{1,3\}\.\)\{3\}[0-9]\{1,3\}   ocfs2-host2:" + vm2.get_vm().vmNics[0].ip + "   ocfs2-host2:g\" /etc/hosts"
    exec_cmd_in_vm(vm2, cmd, "change vm2 hostname&ip2 failed")
    
    cmd = "sed -i \"/number = 0/,/name = ocfs2-host1/s/ip_address = \([0-9]\{1,3\}\.\)\{3\}[0-9]\{1,3\}/ip_address = " + vm1.get_vm().vmNics[0].ip + "/g\" /etc/ocfs2/cluster.conf"
    exec_cmd_in_vm(vm1, cmd, "modify ip1 in /etc/ocfs2/cluster.conf failed")

    cmd = "sed -i \"/number = 1/,/name = ocfs2-host2/s/ip_address = \([0-9]\{1,3\}\.\)\{3\}[0-9]\{1,3\}/ip_address = " + vm2.get_vm().vmNics[0].ip + "/g\" /etc/ocfs2/cluster.conf"
    exec_cmd_in_vm(vm1, cmd, "modify ip2 in /etc/ocfs2/cluster.conf failed")

    cmd = "sed -i \"/number = 0/,/name = ocfs2-host1/s/ip_address = \([0-9]\{1,3\}\.\)\{3\}[0-9]\{1,3\}/ip_address = " + vm1.get_vm().vmNics[0].ip + "/g\" /etc/ocfs2/cluster.conf"
    exec_cmd_in_vm(vm2, cmd, "modify ip1 in /etc/ocfs2/cluster.conf failed")

    cmd = "sed -i \"/number = 1/,/name = ocfs2-host2/s/ip_address = \([0-9]\{1,3\}\.\)\{3\}[0-9]\{1,3\}/ip_address = " + vm2.get_vm().vmNics[0].ip + "/g\" /etc/ocfs2/cluster.conf"
    exec_cmd_in_vm(vm2, cmd, "modify ip2 in /etc/ocfs2/cluster.conf failed")

    cmd = "hostnamectl set-hostname ocfs2-host2"
    exec_cmd_in_vm(vm2, cmd, "%s failed" %(cmd))

    cmd = "systemctl enable o2cb.service"
    exec_cmd_in_vm(vm1, cmd, "%s failed" %(cmd))
    exec_cmd_in_vm(vm2, cmd, "%s failed" %(cmd))

    cmd = "systemctl enable ocfs2.service"
    exec_cmd_in_vm(vm1, cmd, "%s failed" %(cmd))
    exec_cmd_in_vm(vm2, cmd, "%s failed" %(cmd))

    cmd = "systemctl restart o2cb.service"
    exec_cmd_in_vm(vm1, cmd, "%s failed" %(cmd))
    exec_cmd_in_vm(vm2, cmd, "%s failed" %(cmd))

    cmd = "o2cb.init online"
    exec_cmd_in_vm(vm1, cmd, "%s failed" %(cmd))
    ensure_storage_online(vm1)

    exec_cmd_in_vm(vm2, cmd, "%s failed" %(cmd))
    ensure_storage_online(vm2)

    mkfs_sharable_volume(vm1)

    cmd = "mount.ocfs2 /dev/sda /opt/smp/disk1/"
    exec_cmd_in_vm(vm1, cmd, "%s failed" %(cmd))
    exec_cmd_in_vm(vm2, cmd, "%s failed" %(cmd))



def check_sharable_volume(vm1, vm2):
    """
    This function touch a file named "tag1" in vm1, and then check the tag existence from vm2
    """

    cmd = "touch /opt/smp/disk1/tag1"
    exec_cmd_in_vm(vm1, cmd, "%s failed" %(cmd))

    cmd = "test -f /opt/smp/disk1/tag1"
    exec_cmd_in_vm(vm2, cmd, "%s failed" %(cmd))
    

def test():
    test_util.test_dsc('Create test vm and check')
    vm1 = test_stub.create_vm(vm_name="vm1", image_name="ocfs2-host-image")
    test_obj_dict.add_vm(vm1)

    vm2 = test_stub.create_vm(vm_name="vm2", image_name="ocfs2-host-image")
    test_obj_dict.add_vm(vm2)

    test_util.test_dsc('Create volume and check')
    disk_offering = test_lib.lib_get_disk_offering_by_name(os.environ.get('rootDiskOfferingName'))
    volume_creation_option = test_util.VolumeOption()
    volume_creation_option.set_disk_offering_uuid(disk_offering.uuid)
    volume_creation_option.set_system_tags(['ephemeral::shareable', 'capability::virtio-scsi'])

    volume = test_stub.create_volume(volume_creation_option)
    test_obj_dict.add_volume(volume)
    volume.check()

    test_util.test_dsc('Attach volume and check')
    #mv vm checker later, to save some time.
    vm1.check()
    vm2.check()
    volume.attach(vm1)
    volume.attach(vm2)

    config_ocfs2_vms(vm1, vm2)
    check_sharable_volume(vm1, vm2)
    volume.check()

    #test_util.test_dsc('Detach volume and check')
    #volume.detach(vm1.get_vm().uuid)
    #volume.detach(vm2.get_vm().uuid)
    #volume.check()

    sv_cond = res_ops.gen_query_conditions("volumeUuid", '=', volume.get_volume().uuid)
    share_volume_vm_uuid_objs = res_ops.query_resource_fields(res_ops.SHARE_VOLUME, sv_cond, None, fields=['vmInstanceUuid']) 
    share_volume_vm_uuids = []
    for vm_uuid_obj in share_volume_vm_uuid_objs:
        share_volume_vm_uuids.append(vm_uuid_obj.vmInstanceUuid)

    if vm1.get_vm().uuid not in share_volume_vm_uuids:
        test_util.test_fail("target vm uuid: %s; but the attached vm list is %s" %(vm1.get_vm().uuid, str(share_volume_vm_uuids))) 

    test_util.test_dsc('Delete volume and check')
    vm1.destroy()
    vm1.expunge()
    vm1.check()
    test_obj_dict.rm_volume(volume)

    share_volume_vm_uuid_objs = res_ops.query_resource_fields(res_ops.SHARE_VOLUME, sv_cond, None, fields=['vmInstanceUuid']) 
    share_volume_vm_uuids = []
    for vm_uuid_obj in share_volume_vm_uuid_objs:
        share_volume_vm_uuids.append(vm_uuid_obj.vmInstanceUuid)
    if vm1.get_vm().uuid in share_volume_vm_uuids:
        test_util.test_fail("deleted vm still have shareable volume attached to it.") 

    vm2.destroy()
    vm2.check()
    vm2.expunge()
    test_util.test_pass('Create Data Volume for VM Test Success')

#Will be called only if exception happens in test().
def error_cleanup():
    test_lib.lib_error_cleanup(test_obj_dict)
