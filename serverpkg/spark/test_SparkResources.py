from unittest import TestCase
from SparkResources import SparkResources


class StubQuery:
    """This class replaces the SparkAdminQuery"""
    def __init__(self, applist=[]):
        self.applist = applist
    def get_spark_app_list(self):
        return self.applist

class TestSparkResources(TestCase):
    def setUp(self):
        self.rm = SparkResources(cluster_name='testcluster',
                                 app_config={'allowed_submitter_id': ["4444"]},
                                 priv_key_path=".")
        # replace the real Query class with a stub
        self.rm.query = StubQuery()

    def tearDown(self):
        self.rm.ongoing_tasks.drop_table()

    def test_allow_user_to_submit(self):
        # submit on empty stomach
        self.assertFalse(self.rm.allow_user_to_submit('123')['ok'])
        self.assertTrue(self.rm.allow_user_to_submit('4444')['ok'])

    def test_allow_user_to_submit_too_full1(self):
        # add some batches but no app_id
        user = "4444"
        self.rm.add_batch_id(user,"5")
        self.rm.add_batch_id(user, "6")
        self.assertTrue(self.rm.allow_user_to_submit(user)['ok'])
        self.rm.add_batch_id(user, "7")
        self.assertFalse(self.rm.allow_user_to_submit(user)['ok'])

    def test_allow_user_to_submit_too_full2(self):
        user = "4444"
        self.rm.add_batch_id(user,"5")
        self.rm.add_batch_id(user, "6")
        self.rm.add_batch_id(user, "7")
        self.rm.add_app_id(user,6,"app 6")
        self.rm.add_app_id(user, 7, "app 7")
        self.rm.add_app_id(user, 5, "app 5")
        self.rm.query.applist = ["app 5","app 7" ,"app 6" ]
        self.assertFalse(self.rm.allow_user_to_submit(user)['ok'])
        # now mark two of the 3 apps as still running, so we should be allowed to submit
        self.rm.query.applist = ["app 5","app 7"]
        self.assertTrue(self.rm.allow_user_to_submit(user)['ok'])

        # make sure we are left with the correct app ids
        self.assertEqual("{ 4444:app 7, 4444:app 5,  }", self.rm.dump_state())

    def test_mixed_users(self):
        user = "4444"
        self.rm.add_batch_id(user, "5")
        self.rm.add_batch_id("123", "6")
        self.rm.add_batch_id(user, "7")
        self.rm.add_app_id("123", 6, "app 6")
        self.rm.add_app_id(user, 7, "app 7")
        self.rm.add_app_id(user, 5, "app 5")
        self.rm.query.applist = ["app 5", "app 7", "app 6"]
        self.assertTrue(self.rm.allow_user_to_submit(user)['ok'])
        self.rm.add_batch_id(user, "8")
        self.rm.add_app_id(user, 8, "app 8")
        # now mark two of the 3 apps as still running, so we should be allowed to submit
        self.rm.query.applist = ["app 5", "app 7", "app 8"]
        self.assertFalse(self.rm.allow_user_to_submit(user)['ok'])

    def test_add_batch_id(self):
        user = "4444"
        self.rm.add_batch_id(user, "5")
        self.rm.add_batch_id(user, "6")
        self.assertEqual("{ 4444:5, 4444:6,  }", self.rm.dump_state())

    def test_add_app_id(self):
        user = "4444"
        self.rm.add_batch_id(user, "5")
        self.rm.add_batch_id(user, "7")
        self.rm.add_batch_id(user, "6")
        self.rm.add_app_id(user, 5, "app 5")
        self.rm.add_app_id(user, 6, "app 6")
        self.assertEqual("{ 4444:7, 4444:app 5, 4444:app 6,  }", self.rm.dump_state())


    def _test_remove_job(self):
        self.fail()
