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
Tests For Periodic Check.
"""
import time

from oslo.config import cfg

from nova import context as context_maker
from nova import test
from nova import db
from nova.openstack.common import periodic_task
from nova.scheduler import periodic_checks as pc

# test_opts = [
#     cfg.StrOpt('check_server',
#                help='Attestation server HTTP'),
#     cfg.StrOpt('port',
#                default='8443',
#                help='Attestation server port'),
#     cfg.IntOpt('spacing',
#                default=60,
#                help='Attestation status cache valid period length'),
#     cfg.StrOpt('status',
#                default='trust_off',
#                help='Attestation status for turn off or on'),
# ]

CONF = cfg.CONF
test_group = cfg.OptGroup(name='test',
                           title='test')
CONF.register_group(test_group)
# CONF.register_opts(test_opts, group=test_group)

class FakeRequest(object):
    environ = {"nova.context": context_maker.get_admin_context()}
    GET = {}

class PeriodicTestCase(test.TestCase):
    """Test case for host adapters."""
    USES_DB = True
    periodic_cls =  pc.PeriodicChecks
    driver_cls_name = 'nova.scheduler.driver.Scheduler'
    

    def setUp(self):
        super(PeriodicTestCase, self).setUp()
        self.flags(scheduler_driver=self.driver_cls_name)
        self.periodic = self.periodic_cls()
        self.req = FakeRequest()
    def test__init__(self):
        self.assertEqual(2,self.periodic.check_times)

    def test_periodic_task(self):
        res = self.periodic.run_checks({})
    	self.assertEqual(3,res)
        
    def test_periodic_utils(self):
        @periodic_task.periodic_task(spacing=5,run_immediately=True)
        def run_sample_checks():
            return "100"
        self.assertEqual("100", run_sample_checks())
    	
    def test_compute_pool_init(self):
        compute_nodes = self.periodic.compute_nodes
        self.assertFalse(compute_nodes,None)

    def test_periodic_checks_off(self):
        ''' Test that when component is turned off, it returns None as the
        compute pool
        '''
        self.periodic.turn_off_periodic_check()
        self.assertEqual(None,self.periodic.get_trusted_pool())

    def test_periodic_checks_on(self):
        ''' Test that when component is turned on, it does not return None as the
        compute pool
        '''
        self.periodic.turn_off_periodic_check()
        self.periodic.turn_on_periodic_check()
        time.sleep(5)
        self.assertFalse(None,self.periodic.get_trusted_pool())

    def test_add_check(self):
        self.req.environ["nova.context"].is_admin = True
        dc = {'check_id':'test', 'time_out' : '10', 'port' : '5534', 'status' : 'turn_off', 'server':'localhost'}
        self.periodic.add_check(self.req.environ["nova.context"], dc)
        test_check = self.periodic.get_check_by_id(self.req.environ["nova.context"], dc)
        self.assertEqual(test_check['check_id'], 'test')
        #db.periodic_check_delete(self.req.environ["nova.context"], dc['check_id'])
