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
"""
Tests For Host Adapter.
"""

import httplib
import stubout

from nova import test
from nova import context
from nova import servicegroup
from nova.scheduler import adapters
from nova.tests.scheduler import fakes
from nova.openstack.common import timeutils
from nova.scheduler.adapters import attestation_adapter



class AdapterTestCase(test.NoDBTestCase):
    """Test case for host adapters."""
    USES_DB = True

    def fake_oat_request(self, *args, **kwargs):
        """Stubs out the response from OAT service."""
        return httplib.OK, self.oat_data

    def setUp(self):
        super(AdapterTestCase, self).setUp()
        self.oat_data = ''
        self.stubs = stubout.StubOutForTesting()
        self.stubs.Set(attestation_adapter.AttestationService, '_request',
                self.fake_oat_request)
        self.context = context.RequestContext('fake', 'fake')
        adapter_handler = adapters.AdapterHandler()
        classes = adapter_handler.get_matching_classes(
                ['nova.scheduler.adapters.all_adapters'])
        self.class_map = {}
        for cls in classes:
            self.class_map[cls.__name__] = cls

    def test_all_adapters(self):
        # Double check at least a known adapter exist
        self.assertIn('ComputeAttestationAdapter', self.class_map)

    def _stub_service_is_up(self, ret_value):
        def fake_service_is_up(self, service):
                return ret_value
        self.stubs.Set(servicegroup.API, 'service_is_up', fake_service_is_up)

    def _set_oat_trusted(self, trusted_stats):
        self.oat_data = {"hosts": [{"host_name": "host1",
                           "trust_lvl": trusted_stats,
                           "vtime": timeutils.isotime()}]}
        

    def test_attestation_adapter_and_trusted(self):
        
        self._set_oat_trusted('trusted')
        self._stub_service_is_up(True)
        adapter_cls = self.class_map['ComputeAttestationAdapter']()
        extra_specs = {'trust:trusted_host': 'trusted'}
        host_state = fakes.FakeHostState('host1', 'node1', {})
        self.assertTrue(adapter_cls.is_trusted(host_state.host, extra_specs.get('trust:trusted_host')))

    def test_attestation_adapter_and_untrusted(self):

        self._set_oat_trusted('untrusted')
        self._stub_service_is_up(True)
        adapter_cls = self.class_map['ComputeAttestationAdapter']()
        extra_specs = {'trust:trusted_host': 'trusted'}
        host_state = fakes.FakeHostState('host2', 'node1', {})
        self.assertFalse(adapter_cls.is_trusted(host_state.host, extra_specs.get('trust:trusted_host')))

    def test_attestation_adapter_and_unknown(self):

        self._set_oat_trusted('unknown')
        self._stub_service_is_up(True)
        adapter_cls = self.class_map['ComputeAttestationAdapter']()
        extra_specs = {'trust:trusted_host': 'trusted'}
        host_state = fakes.FakeHostState('host3', 'node1', {})
        self.assertFalse(adapter_cls.is_trusted(host_state.host, extra_specs.get('trust:trusted_host')))


