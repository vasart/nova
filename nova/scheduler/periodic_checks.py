
from nova.openstack.common import log as logging
from nova.scheduler import driver

LOG = logging.getLogger(__name__)

class PeriodicChecks(object):
    '''
    This module contains 4 main functions:
        1. Accept user input through Nova API to create, update and delete checks
        2. Store checks and their parameters inside Ceilometer using (Ceilometer API?)
        3. Communicate with adapters for each running check
        4. Communicate with trusted_filer.py to provide it with a trusted compute pool 
            periodically or when user asks for get_trusted_pool
    This component also mediates communication with OpenAttestation (OA) for the trusted_filter
    unless it is not running, in which case the trusted_filter will call OA directly.             
    '''
    # map of nodes and their trusted status
    all_nodes = {}
    
    # list of running checks
    running_checks = [] 
    
    # periodic tasks not running by default
    periodic_tasks_running = False;
    
    # list of weighed nodes received from filter_scheduler
    weighed_hosts = {}
    
    ''' @param:   '''
    def __init__(self):
        ''' 
        TODO:
            a. Get information about checks from Ceilometer
            b. Initialize adapters for each check
            c. Communicate with trusted_filter and let it know of my existence
        '''
        
        # periodic tasks are now running
        PeriodicChecks.periodic_tasks_running = True;
        
        
        
    def get_trusted_pool(self):
        # TODO return the local trusted pool
        return {} 

    def add_Check(self, *args, **kwargs):
        spacing = kwargs['spacing']
        type_of_check = kwargs['type_of_check'] 
        ''' negative time spacing will deactivate the periodic check '''
        @periodic_task.periodictask(spacing, run_immediately = True)
        def run_check(self):
            # @david TODO update pool based on value returned by adapter
            pass
        return run_check    
    
    def removeCheck(self):
        #  stop and delete adapter for this check and update Ceilometer database
        pass
    
    def acceptAdapterMessage(self):
        # update the local trusted pool
        pass
    
    def is_periodic_checks_running(self):
        if PeriodicChecks.periodic_tasks_running:
            return True;
        return False;


    @periodic_task.periodic_task(spacing=CONF.scheduler_driver_task_period,
                                 run_immediately=True)
    def _run_periodic_tasks(self, context):
        self.driver.run_periodic_tasks(context)
    