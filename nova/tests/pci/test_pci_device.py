# Copyright 2014 Intel Corporation
# All Rights Reserved.
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

from nova import context
from nova import exception
from nova.objects import instance
from nova.objects import pci_device as pci_device_obj
from nova.pci import pci_device
from nova import test


dev_dict = {
    'created_at': None,
    'updated_at': None,
    'deleted_at': None,
    'deleted': None,
    'id': 1,
    'compute_node_id': 1,
    'address': 'a',
    'vendor_id': 'v',
    'product_id': 'p',
    'dev_type': 't',
    'status': 'available',
    'dev_id': 'i',
    'label': 'l',
    'instance_uuid': None,
    'extra_info': '{}',
    }


class PciDeviceTestCase(test.TestCase):
    def setUp(self):
        super(PciDeviceTestCase, self).setUp()
        self.ctxt = context.get_admin_context()
        self.inst = instance.Instance()
        self.inst.uuid = 'fake-inst-uuid'
        self.inst.pci_devices = pci_device_obj.PciDeviceList()
        self.devobj = pci_device_obj.PciDevice._from_db_object(
            self.ctxt,
            pci_device_obj.PciDevice(),
            dev_dict)

    def test_claim_device(self):
        pci_device.claim(self.devobj, self.inst)
        self.assertEqual(self.devobj.status, 'claimed')
        self.assertEqual(self.devobj.instance_uuid,
                         self.inst.uuid)
        self.assertEqual(len(self.inst.pci_devices), 0)

    def test_claim_device_fail(self):
        self.devobj.status = 'allocated'
        self.assertRaises(exception.PciDeviceInvalidStatus,
                          pci_device.claim, self.devobj, self.inst)

    def test_allocate_device(self):
        pci_device.claim(self.devobj, self.inst)
        pci_device.allocate(self.devobj, self.inst)
        self.assertEqual(self.devobj.status, 'allocated')
        self.assertEqual(self.devobj.instance_uuid, 'fake-inst-uuid')
        self.assertEqual(len(self.inst.pci_devices), 1)
        self.assertEqual(self.inst.pci_devices[0]['vendor_id'], 'v')
        self.assertEqual(self.inst.pci_devices[0]['status'], 'allocated')

    def test_allocacte_device_fail_status(self):
        self.devobj.status = 'removed'
        self.assertRaises(exception.PciDeviceInvalidStatus,
                          pci_device.allocate,
                          self.devobj,
                          self.inst)

    def test_allocacte_device_fail_owner(self):
        inst_2 = instance.Instance()
        inst_2.uuid = 'fake-inst-uuid-2'
        pci_device.claim(self.devobj, self.inst)
        self.assertRaises(exception.PciDeviceInvalidOwner,
                          pci_device.allocate,
                          self.devobj, inst_2)

    def test_free_claimed_device(self):
        pci_device.claim(self.devobj, self.inst)
        pci_device.free(self.devobj, self.inst)
        self.assertEqual(self.devobj.status, 'available')
        self.assertIsNone(self.devobj.instance_uuid)

    def test_free_allocated_device(self):
        pci_device.claim(self.devobj, self.inst)
        pci_device.allocate(self.devobj, self.inst)
        self.assertEqual(len(self.inst.pci_devices), 1)
        pci_device.free(self.devobj, self.inst)
        self.assertEqual(len(self.inst.pci_devices), 0)
        self.assertEqual(self.devobj.status, 'available')
        self.assertIsNone(self.devobj.instance_uuid)

    def test_free_device_fail(self):
        self.devobj.status = 'removed'
        self.assertRaises(exception.PciDeviceInvalidStatus,
                          pci_device.free, self.devobj)

    def test_remove_device(self):
        pci_device.remove(self.devobj)
        self.assertEqual(self.devobj.status, 'removed')
        self.assertIsNone(self.devobj.instance_uuid)

    def test_remove_device_fail(self):
        pci_device.claim(self.devobj, self.inst)
        self.assertRaises(exception.PciDeviceInvalidStatus,
                          pci_device.remove, self.devobj)
