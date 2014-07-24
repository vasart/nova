# Copyright 2013 OpenStack Foundation
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

import mock

from eventlet import greenthread

from nova import exception
from nova import test
from nova.tests.virt.xenapi import stubs
from nova.virt.xenapi import volume_utils


class SROps(stubs.XenAPITestBaseNoDB):
    def test_find_sr_valid_uuid(self):
        self.session = mock.Mock()
        self.session.call_xenapi.return_value = 'sr_ref'
        self.assertEqual(volume_utils.find_sr_by_uuid(self.session,
                                                      'sr_uuid'),
                         'sr_ref')

    def test_find_sr_invalid_uuid(self):
        class UUIDException(Exception):
            details = ["UUID_INVALID", "", "", ""]

        self.session = mock.Mock()
        self.session.XenAPI.Failure = UUIDException
        self.session.call_xenapi.side_effect = UUIDException
        self.assertEqual(volume_utils.find_sr_by_uuid(self.session,
                                                      'sr_uuid'),
                         None)


class ISCSIParametersTestCase(stubs.XenAPITestBaseNoDB):
    def test_target_host(self):
        self.assertEqual(volume_utils._get_target_host('host:port'),
                         'host')

        self.assertEqual(volume_utils._get_target_host('host'),
                         'host')

        # There is no default value
        self.assertEqual(volume_utils._get_target_host(':port'),
                         None)

        self.assertEqual(volume_utils._get_target_host(None),
                         None)

    def test_target_port(self):
        self.assertEqual(volume_utils._get_target_port('host:port'),
                         'port')

        self.assertEqual(volume_utils._get_target_port('host'),
                         '3260')


class IntroduceTestCase(stubs.XenAPITestBaseNoDB):

    @mock.patch.object(volume_utils, '_get_vdi_ref')
    @mock.patch.object(greenthread, 'sleep')
    def test_introduce_vdi_retry(self, mock_sleep, mock_get_vdi_ref):
        def fake_get_vdi_ref(session, sr_ref, vdi_uuid, target_lun):
            fake_get_vdi_ref.call_count += 1
            if fake_get_vdi_ref.call_count == 2:
                return 'vdi_ref'

        def fake_call_xenapi(method, *args):
            if method == 'SR.scan':
                return
            elif method == 'VDI.get_record':
                return {'managed': 'true'}

        session = mock.Mock()
        session.call_xenapi.side_effect = fake_call_xenapi

        mock_get_vdi_ref.side_effect = fake_get_vdi_ref
        fake_get_vdi_ref.call_count = 0

        self.assertEqual(volume_utils.introduce_vdi(session, 'sr_ref'),
                         'vdi_ref')
        mock_sleep.assert_called_once_with(20)

    @mock.patch.object(volume_utils, '_get_vdi_ref')
    @mock.patch.object(greenthread, 'sleep')
    def test_introduce_vdi_exception(self, mock_sleep, mock_get_vdi_ref):
        def fake_call_xenapi(method, *args):
            if method == 'SR.scan':
                return
            elif method == 'VDI.get_record':
                return {'managed': 'true'}

        session = mock.Mock()
        session.call_xenapi.side_effect = fake_call_xenapi
        mock_get_vdi_ref.return_value = None

        self.assertRaises(exception.StorageError,
                          volume_utils.introduce_vdi, session, 'sr_ref')
        mock_sleep.assert_called_once_with(20)


class ParseVolumeInfoTestCase(stubs.XenAPITestBaseNoDB):
    def test_mountpoint_to_number(self):
        cases = {
            'sda': 0,
            'sdp': 15,
            'hda': 0,
            'hdp': 15,
            'vda': 0,
            'xvda': 0,
            '0': 0,
            '10': 10,
            'vdq': -1,
            'sdq': -1,
            'hdq': -1,
            'xvdq': -1,
        }

        for (input, expected) in cases.iteritems():
            actual = volume_utils._mountpoint_to_number(input)
            self.assertEqual(actual, expected,
                    '%s yielded %s, not %s' % (input, actual, expected))

    @classmethod
    def _make_connection_info(cls):
        target_iqn = 'iqn.2010-10.org.openstack:volume-00000001'
        return {'driver_volume_type': 'iscsi',
                'data': {'volume_id': 1,
                         'target_iqn': target_iqn,
                         'target_portal': '127.0.0.1:3260,fake',
                         'target_lun': None,
                         'auth_method': 'CHAP',
                         'auth_username': 'username',
                         'auth_password': 'password'}}

    def test_parse_volume_info_parsing_auth_details(self):
        conn_info = self._make_connection_info()
        result = volume_utils._parse_volume_info(conn_info['data'])

        self.assertEqual('username', result['chapuser'])
        self.assertEqual('password', result['chappassword'])

    def test_get_device_number_raise_exception_on_wrong_mountpoint(self):
        self.assertRaises(
            exception.StorageError,
            volume_utils.get_device_number,
            'dev/sd')


class FindVBDTestCase(stubs.XenAPITestBaseNoDB):
    def test_find_vbd_by_number_works(self):
        session = mock.Mock()
        session.VM.get_VBDs.return_value = ["a", "b"]
        session.VBD.get_userdevice.return_value = "1"

        result = volume_utils.find_vbd_by_number(session, "vm_ref", 1)

        self.assertEqual("a", result)
        session.VM.get_VBDs.assert_called_once_with("vm_ref")
        session.VBD.get_userdevice.assert_called_once_with("a")

    def test_find_vbd_by_number_no_matches(self):
        session = mock.Mock()
        session.VM.get_VBDs.return_value = ["a", "b"]
        session.VBD.get_userdevice.return_value = "3"

        result = volume_utils.find_vbd_by_number(session, "vm_ref", 1)

        self.assertIsNone(result)
        session.VM.get_VBDs.assert_called_once_with("vm_ref")
        expected = [mock.call("a"), mock.call("b")]
        self.assertEqual(expected,
                         session.VBD.get_userdevice.call_args_list)

    def test_find_vbd_by_number_no_vbds(self):
        session = mock.Mock()
        session.VM.get_VBDs.return_value = []

        result = volume_utils.find_vbd_by_number(session, "vm_ref", 1)

        self.assertIsNone(result)
        session.VM.get_VBDs.assert_called_once_with("vm_ref")
        self.assertFalse(session.VBD.get_userdevice.called)

    def test_find_vbd_by_number_ignores_exception(self):
        session = mock.Mock()
        session.XenAPI.Failure = test.TestingException
        session.VM.get_VBDs.return_value = ["a"]
        session.VBD.get_userdevice.side_effect = test.TestingException

        result = volume_utils.find_vbd_by_number(session, "vm_ref", 1)

        self.assertIsNone(result)
        session.VM.get_VBDs.assert_called_once_with("vm_ref")
        session.VBD.get_userdevice.assert_called_once_with("a")
