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

CONF = cfg.CONF

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

    def test_check_running(self):
        self.assertTrue(CONF.periodic_checks.periodic_tasks_running)
        CONF.periodic_checks.periodic_tasks_running = False
        self.assertFalse(CONF.periodic_checks.periodic_tasks_running)

    def test_periodic_checks_on(self):
        ''' Test that when component is turned on, it does not return None as the
        compute pool
        '''
        self.periodic.turn_off_periodic_check()
        self.periodic.turn_on_periodic_check() 
        time.sleep(5)
        self.assertFalse(None,self.periodic.get_trusted_pool())

    def test_add_check(self):
        ctxt = context_maker.get_admin_context()
        dc = {'check_name':'test_check', 'spacing' : '10', 'port' : '5534', 'status' : 'turn_off', 'server':'localhost', 'description': 'test_check', 'time_out' : 10}
        self.periodic.add_check(ctxt, dc)
        test_check = db.periodic_check_get(ctxt, 'test_check')
        self.assertEqual(test_check['check_name'], 'test_check')
        db.periodic_check_delete(ctxt, dc['check_name'])

    def test_remove_check(self):
        ctxt = context_maker.get_admin_context()
        dc = {'check_name':'test_check', 'spacing' : '10', 'port' : '5534', 'status' : 'turn_off', 'server':'localhost', 'description': 'test_check', 'time_out' : 10}
        db.periodic_check_create(ctxt, dc)
        self.periodic.remove_check(ctxt, dc)
        test_check = db.periodic_check_get_all(ctxt)
        self.assertEqual(len(test_check), 0)

    def test_get_all_check(self):
        ctxt = context_maker.get_admin_context()
        dc = {'check_name':'test_check_1', 'spacing' : '10', 'port' : '5534', 'status' : 'turn_off', 'server':'localhost', 'description': 'test check 1', 'time_out' : 10}
        db.periodic_check_create(ctxt, dc)
        dc = {'check_name':'test_check_2', 'spacing' : '10', 'port' : '5534', 'status' : 'turn_off', 'server':'localhost', 'description': 'test check 2', 'time_out' : 10}
        db.periodic_check_create(ctxt, dc)
        test_check = self.periodic.get_all_checks(ctxt)
        self.assertEqual(len(test_check), 2)
        db.periodic_check_delete(ctxt, 'test_check_1')
        db.periodic_check_delete(ctxt, 'test_check_2')

    def test_update_check(self):
        ctxt = context_maker.get_admin_context()
        dc = {'check_name':'test_check', 'spacing' : '10', 'port' : '5534', 'status' : 'turn_off', 'server':'localhost', 'description': 'test_check', 'time_out' : 10}
        db.periodic_check_create(ctxt, dc)
        dc = {'check_name':'test_check', 'spacing' : '20', 'port' : '5534', 'status' : 'turn_off', 'server':'localhost', 'description': 'test check 2', 'time_out' : 10}
        self.periodic.update_check(ctxt, dc)
        test_check = db.periodic_check_get(ctxt, 'test_check')
        self.assertEqual(test_check['spacing'], 20)
        db.periodic_check_delete(ctxt, dc['check_name'])

    def test_get_check_by_name(self):
        ctxt = context_maker.get_admin_context()
        dc = {'check_name':'test_check', 'spacing' : '10', 'port' : '5534', 'status' : 'turn_off', 'server':'localhost', 'description': 'test_check', 'time_out' : 10}
        db.periodic_check_create(ctxt, dc)
        test_check = self.periodic.get_check_by_name(ctxt, dc)
        self.assertEqual(test_check['check_name'], 'test_check')
        db.periodic_check_delete(ctxt, dc['check_name'])  

