from nova.openstack.common import log as logging
from nova.openstack.common import periodic_task
from nova import db
from nova.scheduler import adapters
from nova import context

LOG = logging.getLogger(__name__)

class PeriodicChecks(object):
    '''
    This module contains 4 main functions:
        1. Accept user input through Nova API to create, update and 
                delete checks
        2. Store checks and their parameters inside Ceilometer 
                using (Ceilometer API?)
        3. Communicate with adapters for each running check
        4. Communicate with trusted_filer.py to provide it with a 
                trusted compute pool periodically or when user asks 
                for get_trusted_pool
    This component also mediates communication with OpenAttestation 
            (OA) for the trusted_filter unless it is not running, in 
            which case the trusted_filter will call OA directly.             
    '''

    
    # list of running checks
    running_checks = {} 
    check_times = 0
    
    # periodic tasks not running by default
    periodic_tasks_running = False;
    
    def __init__(self):
        ''' 
        TODO:
            a. Get information about checks from Ceilometer
            b. Initialize adapters for each check
        '''
        admin = context.get_admin_context()
        self.compute_nodes = {}

        # set flag to show that periodic checks are now running
        PeriodicChecks.periodic_tasks_running = True;
        # get all adapters
        self.adapter_handler = adapters.AdapterHandler()
        # get all compute nodes
        self.compute_nodes = db.compute_node_get_all(admin)
        # trust status for each node in the compute pool
        self.node_trust_status ={}
        self._get_all_adapters()
                
    def _get_all_adapters(self):
        classes = self.adapter_handler.get_matching_classes(
                ['nova.scheduler.adapters.all_adapters'])
        class_map = {}
        for cls in classes:
            class_map[cls.__name__] = cls
        return class_map
    
    @periodic_task.periodic_task(spacing=5, run_immediately = True)
    def _run_checks(self, **kwargs):
        # form a temporary compute pool to prevent unavailability of pool during running checks
        trust_status_temp = {}
        for node in self.compute_nodes:
            for adapter in adapters:
                result = adapter.is_trusted(node, 'trusted');
                trust_status_temp[node] = result
        self.node_trust_status = trust_status_temp
        self.check_times += 1
    
    '''
    @param id: identifier for the check
    @param spacing: time between successive checks in seconds
    @param type-of_check: (optional) any additional info about of the check 
    '''
    def add_check(self,**kwargs):
        #check_id = kwargs['id']
        # set the periodic tasks running flag to True
        # TODO write new check into CONF
        PeriodicChecks.periodic_tasks_running = True
    
    def remove_check(self, **kwargs):
        # stop and delete adapter for this check and update Ceilometer database
        check_id = kwargs['id']
        if check_id not in self.running_checks:
            raise Exception("Check is not running")
        else:
            # stop the check
            self.running_checks[check_id] = None
            # remove it from list of running checks
            self.running_checks.pop(check_id)
            # check if there are no checks running
            if len(self.running_checks) == 0:
                PeriodicChecks.periodic_tasks_running = False
            
    def update_check(self, **kwargs):
        check_id = kwargs['id']
        new_spacing = kwargs['spacing']
        self.remove_check({'id':check_id})
        ''' optional: also specify type_of_check'''
        self.add_check({'id':check_id, 'spacing': new_spacing})

    '''
    Used to check of periodic tasks are running by 
        scheduler.filters.trusted_filter
    '''
    def is_periodic_checks_running(self):
        if PeriodicChecks.periodic_tasks_running:
            return True;
        return False;

    def get_running_checks(self):
        return self.running_check;
