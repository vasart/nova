from nova import test
from oslo.config import cfg

class PeriodicChecksTestCase(test.NoDBTestCase):
    """Test case for Periodic Checks class."""
    
    def setUp(self):
        super(SchedulerManagerTestCase, self).setUp()
        self.flags(scheduler_driver=self.driver_cls_name)
        self.stubs.Set(compute_api, 'API', fakes.FakeComputeAPI)
        self.manager = self.manager_cls()
        self.context = context.RequestContext('fake_user', 'fake_project')
        self.topic = 'fake_topic'
        self.fake_args = (1, 2, 3)
        self.fake_kwargs = {'cat': 'meow', 'dog': 'woof'}
        fake_server_actions.stub_out_action_events(self.stubs)
    
    def test_add_check(self):
        pass
        
        