from unittest import TestCase
from workshop_db import WorkshopDb


class TestWorkshopDb(TestCase):
    """
    This test suite checks the Workshop DB class
    We try to verify both good and bad scenarios - such as adding a score before there is submission
    """

    def setUp(self):
        self.w = WorkshopDb()

    def tearDown(self):
        self.w.purge_db()

    def test_try_add_submission(self):
        w = self.w
        with self.assertRaises(KeyError):
            w.add_score('a', 0.1)
        w.try_add_submission('a')
        w.try_add_submission('b')
        w.try_add_submission('b')
        w.try_add_submission('b')
        self.assertTrue(w.get_scores() == {'a': (0.0, 1), 'b': (0.0, 3)})

    def test_try_add_submission_fail(self):
        w = self.w
        self.assertTrue(w.try_add_submission('b'))
        self.assertTrue(w.try_add_submission('b'))
        self.assertTrue(w.try_add_submission('b'))
        self.assertFalse(w.try_add_submission('b'))

    def test_add_score(self):
        self.w.try_add_submission('a')
        self.w.add_score('a', 0.5)
        self.w.try_add_submission('a')
        self.w.add_score('a', 0.2)
        self.assertTrue(self.w.get_scores() == {'a': (0.5, 2)})

    def test_persistency(self):
        w1 = WorkshopDb()
        w1.try_add_submission('c')
        w2 = WorkshopDb()
        self.assertTrue(w2.get_scores() == {'c': (0.0, 1)})
        w2.purge_db()
