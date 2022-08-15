from .PersistDict import PersistMultiDict
from serverpkg.spark.queries import SparkAdminQuery


class SparkResources:
    """Manage number of the running Spark applications.
    It is used when a user wants to submit a job and we need to decide
    if we allow it or not.

    The info on ongoing jobs is kept in a persistent, multi process safe access database
    When trying to add new job, check in the spark server, and decide if it is permitted.
    The actual submission of a new application is NOT done here.

    The flow:
    user wants to add job.
    check how many jobs running for user, including embryos - when there is only batch id but no app id.
     update the list of running jobs with the output of 'yarn status'
    If # < 3, submit new job,
      save the batch id (so user will not be able to rapid fire several jobs before we start seeing them in yarn)
      get the appId (takes a long time) and save to the list of running jobs for this user.
    """
    MAX_CONCURRENT_APPS_PER_USER = 3

    def __init__(self, cluster_name, cluster_url_ssh,cluster_url_https,  allowed_submitters: dict, priv_key_path: str, livy_pass, scheduler):
        self.cluster_name = cluster_name
        self.allowed_submitters = allowed_submitters
        self.ongoing_tasks = PersistMultiDict('ongoing_apps.db', 'singleSparkRM')

        self.query = SparkAdminQuery(cluster_url_ssh_name=cluster_url_ssh,
                                     cluster_url_https=cluster_url_https,
                                     pkey=priv_key_path,
                                     livy_password=livy_pass)

        # add a periodic task to get updates from Spark server
        scheduler.add_job( self._update_running_apps, 'interval', seconds=60)

    def _is_running_app(self, appId: str)-> bool:
        pass

    def allow_user_to_submit(self, user_id):
        """check if the user may submit new job.
        :return { 'ok': True|False, 'reason': str}
        """
        if user_id not in self.allowed_submitters:
            return {'ok': False, 'reason': 'User is not in the allowed submitters whitelist<br>'
                                           'The file name must start with 9 digit ID followed by _'}

        self._update_running_apps()

        user_data = self.ongoing_tasks.get(user_id)['value']
        if len(user_data) == 0:
            return {'ok': True, 'reason': 'User is within budget'}

        if len(user_data) >= SparkResources.MAX_CONCURRENT_APPS_PER_USER:
            return {'ok': False, 'reason': f'User is running the maximum num of apps ({SparkResources.MAX_CONCURRENT_APPS_PER_USER})'}
        return {'ok': True, 'reason': 'User is running less than the maximum number'}

    def add_batch_id(self, user_id, batch_id):
        """A batch ID is returned from Spark immediately after submission.
        We save it here too."""
        self.ongoing_tasks.add(user_id, batch_id)

    def add_app_id(self, user_id, batch_id, application_id)->None:
        """ add an application ID to the list of running jobs.
        This is called only after allow_user_to_submit() gave the OK.

        :param user_id:
        :param batch_id: the batch ID that generated this application_id
        :param application_id:
        """
        self.ongoing_tasks.add(user_id, application_id)
        num_removed = self.ongoing_tasks.remove_kv(user_id,batch_id) # we don't need it anymore
        assert(num_removed == 1)

    def failed_app(self, user_id, batch_id, app_id):
        """We got report that this app failed, so remove from the table.
        It is possible that either of the values is missing, so do not check retval
        """
        self.ongoing_tasks.remove_kv(user_id,batch_id)
        self.ongoing_tasks.remove_kv(user_id, app_id)

    def remove_job(self, user_id, application_id):
        """remove the application_id from the list of ongoing apps
        This only changes the listing of apps, it does not stop an app."""
        num_removed = self.ongoing_tasks.remove_kv(user_id,application_id)
        if num_removed != 1:
            #raise ValueError('bad uid or appid')
            pass

    def _update_running_apps(self):
        """get the list of running apps,
        and use this data to update the state for ALL users."""

        # https://docs.microsoft.com/en-us/rest/api/synapse/data-plane/spark-job-definition/execute-spark-job-definition?tabs=HTTP#livystates
        terminal_state = ('dead','error','killed', 'shutting_down', 'success')
        try:
            sessions = self.query.get_spark_app_list()
        except ConnectionError:
            return

        #running_app_ids = {x['appId'] for x in sessions if x['state'] == 'running'}

        local_app_and_batch_id = set(self.ongoing_tasks.values())

        # and some applicationID will be removed
        local_batch_id = set([x for x in local_app_and_batch_id if not x.startswith('app')])
        #local_app_id = local_app_and_batch_id - local_batch_id

        app_id_to_remove = set([x['appId'] for x in sessions if x['state'] in terminal_state])

        # identify the new appID by their batch ID that is still in the local list.
        # we don't take 'starting' applications since sometime the appId is None
        pairs = set([(x['id'],x['appId']) for x in sessions  if str(x['id']) in local_batch_id and x['state'] == 'running'])
        for pair in pairs:
            uid = self.ongoing_tasks.get_key_from_value(pair[0])
            self.add_app_id(uid,pair[0], pair[1])

        for id_ in app_id_to_remove:
            uid = self.ongoing_tasks.get_key_from_value(id_)
            self.remove_job(uid,id_)

    def dump_state(self) -> str:
        return str(self.ongoing_tasks)
