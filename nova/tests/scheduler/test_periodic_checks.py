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

from nova import test
from nova.openstack.common import periodic_task
from nova.scheduler import periodic_checks as pc


class PeriodicTestCase(test.NoDBTestCase):
    """Test case for host adapters."""
    USES_DB = True
    periodic_cls =  pc.PeriodicChecks
    driver_cls_name = 'nova.scheduler.driver.Scheduler'

    def setUp(self):
        super(PeriodicTestCase, self).setUp()
        self.flags(scheduler_driver=self.driver_cls_name)
        self.periodic = self.periodic_cls()

    def test__init__(self):
        self.assertEqual(1,self.periodic.check_times)

    def test_periodic_task(self):
        res = self.periodic.run_checks({})
    	self.assertEqual(12,res)
        
    def test_periodic_utils(self):
        @periodic_task.periodic_task(spacing=5,run_immediately=True)
        def run_sample_checks():
            return "100"
        self.assertEqual("100", run_sample_checks())
    	

        