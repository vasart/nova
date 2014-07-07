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

from nova.scheduler import adapters
from nova.tests.scheduler import fakes
from nova import test

class AdapterTestCase(test.NoDBTestCase):
    """Test case for host filters."""

    def setUp(self):
        super(AdapterTestCase, self).setUp()
        adapter_handler = adapters.AdapterHandler()
        classes = adapter_handler.get_matching_classes(
                ['nova.scheduler.adapters.all_adapters'])
        self.class_map = {}
        for cls in classes:
            self.class_map[cls.__name__] = cls

    def test_all_adapters(self):
        # Double check at least a known adapter exist
        self.assertIn('ComputeAttestationAdapter', self.class_map)

    def test_attestation_adapter_and_trusted(self):
        adapter_cls = self.class_map['ComputeAttestationAdapter']()
        extra_specs = {'trust:trusted_host': 'trusted'}
        host_state = fakes.FakeHostState('jhapl', 'node1', {})
        self.assertTrue(adapter_cls.is_trusted(host_state.host, extra_specs.get('trust:trusted_host')))

	def test_attestation_adapter_and_unknown(self):
        adapter_cls = self.class_map['ComputeAttestationAdapter']()
        extra_specs = {'trust:trusted_host': 'unknown'}
        host_state = fakes.FakeHostState('testHost', 'node1', {})
        self.assertTrue(adapter_cls.is_trusted(host_state.host, extra_specs.get('trust:trusted_host')))
