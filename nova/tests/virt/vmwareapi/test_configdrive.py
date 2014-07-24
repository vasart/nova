# Copyright 2013 IBM Corp.
# Copyright 2011 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import contextlib
import copy
import fixtures

import mock
import mox

from nova import context
from nova.image import glance
from nova import test
import nova.tests.image.fake
from nova.tests import utils
from nova.tests.virt.vmwareapi import stubs
from nova.virt import fake
from nova.virt.vmwareapi import driver
from nova.virt.vmwareapi import fake as vmwareapi_fake
from nova.virt.vmwareapi import read_write_util
from nova.virt.vmwareapi import vm_util
from nova.virt.vmwareapi import vmops
from nova.virt.vmwareapi import vmware_images


class ConfigDriveTestCase(test.NoDBTestCase):
    def setUp(self):
        super(ConfigDriveTestCase, self).setUp()
        vm_util.vm_refs_cache_reset()
        self.context = context.RequestContext('fake', 'fake', is_admin=False)
        cluster_name = 'test_cluster'
        self.flags(cluster_name=[cluster_name],
                   host_ip='test_url',
                   host_username='test_username',
                   host_password='test_pass',
                   use_linked_clone=False, group='vmware')
        self.flags(vnc_enabled=False)
        vmwareapi_fake.reset(vc=True)
        stubs.set_stubs(self.stubs)
        nova.tests.image.fake.stub_out_image_service(self.stubs)
        self.conn = driver.VMwareVCDriver(fake.FakeVirtAPI)
        self.network_info = utils.get_test_network_info()
        self.vim = vmwareapi_fake.FakeVim()
        self.node_name = '%s(%s)' % (self.conn.dict_mors.keys()[0],
                                     cluster_name)
        image_ref = nova.tests.image.fake.get_valid_image_id()
        self.test_instance = {'node': 'test_url',
                              'vm_state': 'building',
                              'project_id': 'fake',
                              'user_id': 'fake',
                              'name': '1',
                              'kernel_id': '1',
                              'ramdisk_id': '1',
                              'mac_addresses': [
                                  {'address': 'de:ad:be:ef:be:ef'}
                              ],
                              'memory_mb': 8192,
                              'flavor': 'm1.large',
                              'vcpus': 4,
                              'root_gb': 80,
                              'image_ref': image_ref,
                              'host': 'fake_host',
                              'task_state':
                                  'scheduling',
                              'reservation_id': 'r-3t8muvr0',
                              'id': 1,
                              'uuid': 'fake-uuid',
                              'node': self.node_name,
                              'metadata': []}

        (image_service, image_id) = glance.get_remote_image_service(context,
                                    image_ref)
        metadata = image_service.show(context, image_id)
        self.image = {
            'id': image_ref,
            'disk_format': 'vmdk',
            'size': int(metadata['size']),
        }

        class FakeInstanceMetadata(object):
            def __init__(self, instance, content=None, extra_md=None):
                pass

            def metadata_for_config_drive(self):
                return []

        self.useFixture(fixtures.MonkeyPatch(
                'nova.api.metadata.base.InstanceMetadata',
                FakeInstanceMetadata))

        def fake_make_drive(_self, _path):
            pass
        # We can't actually make a config drive v2 because ensure_tree has
        # been faked out
        self.stubs.Set(nova.virt.configdrive.ConfigDriveBuilder,
                       'make_drive', fake_make_drive)

        def fake_upload_iso_to_datastore(iso_path, instance, **kwargs):
            pass
        self.stubs.Set(vmware_images,
                       'upload_iso_to_datastore',
                       fake_upload_iso_to_datastore)

    def tearDown(self):
        super(ConfigDriveTestCase, self).tearDown()
        vmwareapi_fake.cleanup()
        nova.tests.image.fake.FakeImageService_reset()

    def _spawn_vm(self, injected_files=None, admin_password=None,
                  block_device_info=None):

        injected_files = injected_files or []
        read_file_handle = mock.MagicMock()
        write_file_handle = mock.MagicMock()
        self.image_ref = self.instance['image_ref']

        def fake_read_handle(read_iter):
            return read_file_handle

        def fake_write_handle(host, dc_name, ds_name, cookies,
                 file_path, file_size, scheme="https"):
            self.assertEqual('dc1', dc_name)
            self.assertEqual('ds1', ds_name)
            self.assertEqual('Fake-CookieJar', cookies)
            split_file_path = file_path.split('/')
            self.assertEqual('vmware_temp', split_file_path[0])
            self.assertEqual(self.image_ref, split_file_path[2])
            self.assertEqual(('%s-flat.vmdk' % self.image_ref),
                             split_file_path[3])
            self.assertEqual(int(self.image['size']), file_size)

            return write_file_handle

        with contextlib.nested(
             mock.patch.object(read_write_util, 'VMwareHTTPWriteFile',
                               side_effect=fake_write_handle),
             mock.patch.object(read_write_util, 'GlanceFileRead',
                                side_effect=fake_read_handle),
             mock.patch.object(vmware_images, 'start_transfer')
        ) as (fake_http_write, fake_glance_read, fake_start_transfer):
            self.conn.spawn(self.context, self.instance, self.image,
                        injected_files=injected_files,
                        admin_password=admin_password,
                        network_info=self.network_info,
                        block_device_info=block_device_info)
            fake_start_transfer.assert_called_once_with(self.context,
                read_file_handle, self.image['size'],
                write_file_handle=write_file_handle)

    def test_create_vm_with_config_drive_verify_method_invocation(self):
        self.instance = copy.deepcopy(self.test_instance)
        self.instance['config_drive'] = True
        self.mox.StubOutWithMock(vmops.VMwareVMOps, '_create_config_drive')
        self.mox.StubOutWithMock(vmops.VMwareVMOps, '_attach_cdrom_to_vm')
        self.conn._vmops._create_config_drive(self.instance,
                                               mox.IgnoreArg(),
                                               mox.IgnoreArg(),
                                               mox.IgnoreArg(),
                                               mox.IgnoreArg(),
                                               mox.IgnoreArg(),
                                               mox.IgnoreArg()
                                               ).AndReturn('[ds1] fake.iso')
        self.conn._vmops._attach_cdrom_to_vm(mox.IgnoreArg(),
                                               mox.IgnoreArg(),
                                               mox.IgnoreArg(),
                                               mox.IgnoreArg())
        self.mox.ReplayAll()
        # if spawn does not call the _create_config_drive or
        # _attach_cdrom_to_vm call with the correct set of parameters
        # then mox's VerifyAll will throw a Expected methods never called
        # Exception
        self._spawn_vm()

    def test_create_vm_without_config_drive(self):
        self.instance = copy.deepcopy(self.test_instance)
        self.instance['config_drive'] = False
        self.mox.StubOutWithMock(vmops.VMwareVMOps, '_create_config_drive')
        self.mox.StubOutWithMock(vmops.VMwareVMOps, '_attach_cdrom_to_vm')
        self.mox.ReplayAll()
        # if spawn ends up calling _create_config_drive or
        # _attach_cdrom_to_vm then mox will log a Unexpected method call
        # exception
        self._spawn_vm()

    def test_create_vm_with_config_drive(self):
        self.instance = copy.deepcopy(self.test_instance)
        self.instance['config_drive'] = True
        self._spawn_vm()
