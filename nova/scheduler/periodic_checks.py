
from nova.openstack.common import log as logging
from nova.scheduler import driver

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
    # map of nodes and their trusted status
    compute_nodes = {}
    
    # list of running checks
    running_checks = {} 
    
    # periodic tasks not running by default
    periodic_tasks_running = False;
    
    def __init__(self):
        ''' 
        TODO:
            a. Get information about checks from Ceilometer
            b. Initialize adapters for each check
        '''
        # set flag to show that periodic checks are now running
        PeriodicChecks.periodic_tasks_running = True;
        
    def get_trusted_pool(self):
        # TODO return the local trusted pool
        return {} 
    ''' 
    This method is not to be called directly. It should be called through 
        add_check()
    @return: reference to run_check() method
    '''
    def run_check_wrapper(self, **kwargs):
        check_id=kwargs['id']
        spacing = kwargs['spacing']
        type_of_check = kwargs['type_of_check'] 
        ''' negative time spacing will deactivate the periodic check '''
        @periodic_task.periodictask(spacing, run_immediately = True)
        def run_check(self):
            # @david TODO update pool based on value returned by adapter
            print "run_check called with args=",args," and kwargs=",kwargs
        return run_check    
    
    '''
    @param id: identifier for the check
    @param spacing: time between successive checks in seconds
    @param type-of_check: (optional) any additional info about of the check 
    '''
    def add_check(self,**kwargs):
        check_id = kwargs['id']
        running_checks[check_id] = run_check_wrapper(self, **kwargs)
        running_checks[check_id]()
        # set the periodic tasks running flag to True
        PeriodicChecks.periodic_tasks_running = True
    
    def removeCheck(self, **kwargs):
        # stop and delete adapter for this check and update Ceilometer database
        check_id = kwargs['id']
        if check_id not in running_checks:
            raise Exception("Check is not running")
        else:
            # stop the check
            running_checks[check_id] = None
            # remove it from list of running checks
            running_checks.pop(check_id)
            # check if there are no checks running
            if len(running_checks) == 0:
                PeriodicChecks.periodic_tasks_running = False
            
    def update_check(self, **kwargs):
        check_id = kwargs['id']
        new_spacing = kwargs['spacing']
        remove_check({'id':check_id})
        ''' optional: also specify type_of_check'''
        add_check({'id':check_id, 'spacing': new_spacing})

    '''
    Used to check of periodic tasks are running by 
        scheduler.filters.trusted_filter
    '''
    def is_periodic_checks_running(self):
        if PeriodicChecks.periodic_tasks_running:
            return True;
        return False;

    def get_running_checks(self):
        return running_check;