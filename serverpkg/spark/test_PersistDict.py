from unittest import TestCase
from PersistDict import PersistDict


class TestPersistDict(TestCase):
    """persists key-> value.
    type(value)  must be str. If you need something else, use json.dumps()
    """

    def setUp(self):
        """ I wanted to use memory db, but it requires to reuse the same connection:
           When this is done, no disk file is opened.
            Instead, a new database is created purely in memory.
            The database ceases to exist as soon as the database connection is closed.
            Every :memory: database is distinct from every other."""
        self.dict = PersistDict("remove_me.sql", "test")

    def tearDown(self) -> None:
        self.dict.drop_table()

    def test_add(self):
        self.dict.add(123, "value123")
        self.assertTrue(123 in self.dict)

    def test_update(self):
        self.dict.add(123, "value123")
        self.dict.add(123, "second")
        self.assertEqual(self.dict.get(123)['value'], "second")

    def test_remove(self):
        self.dict.add(123, "value123")
        self.assertEqual(self.dict.get(123)['value'], "value123")
        self.assertEqual(1, self.dict.remove(123))
        self.assertEqual(self.dict.get(123), None)
        self.assertFalse(123 in self.dict)

    def test_remove_not_found(self):
        self.dict.add(123, "value123")
        self.assertEqual(0, self.dict.remove(55))

    def test_get(self):
        self.dict.add(123, "value123")
        self.dict.add("wow", "value_wow")
        self.assertEqual(self.dict.get("wow")['value'], "value_wow")

    def test_get_not_found(self):
        self.dict.add(123, "value123")
        self.assertEqual(self.dict.get("wow"), None)

    def disabled_test_add_complex_value(self):
        v = {'one': 1, 2: ['a', 'b']}
        self.dict.add(123, v)
        v2 = self.dict.get(123)['value']
        self.assertEqual(dict, type(v2))
        self.assertTrue(v2 == v)



