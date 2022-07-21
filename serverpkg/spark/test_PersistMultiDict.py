from unittest import TestCase
from PersistDict import PersistMultiDict

class TestPersistMultiDict(TestCase):
    def setUp(self):
        self.dict = PersistMultiDict("remove_me.sql", "test")

    def tearDown(self):
        self.dict.drop_table()

    def test_add1(self):
        self.dict.add(123, "value123")
        self.assertTrue(123 in self.dict)

    def test_add3(self):
        self.dict.add("aa", "value a")
        self.dict.add("b", "value b")
        self.dict.add("aa", "value a2")
        self.dict.add("aa", "value a3")
        self.assertTrue("b" in self.dict)
        self.assertTrue("aa" in self.dict)
        values = self.dict.get('aa')['value']
        self.assertTrue(len(values) == 3)
        self.assertEqual("value a2", values[1])

    def test_remove_all(self):
        self.dict.add(123, "value123")
        self.dict.add(123, "value 4")
        self.assertEqual(2, self.dict.remove(123))
        self.assertEqual([], self.dict.get(123)['value'])
        self.assertFalse(123 in self.dict)

    def test_remove_one(self):
        self.dict.add(123, "value123")
        self.dict.add(123, "value 4")
        self.assertEqual(1, self.dict.remove_kv(123,"value 4"))
        self.assertEqual(["value123"], self.dict.get(123)['value'])
        self.assertTrue(123 in self.dict)
        self.assertEqual(0, self.dict.remove_kv(123, "value 4")) # already deleted
        self.assertEqual(1, self.dict.remove_kv(123, "value123"))
        self.assertFalse(123 in self.dict)

    def test_dump(self):
        """test that the debug print is correct"""
        self.dict.add(123, "value123")
        self.dict.add(123, "value 4")
        self.dict.add("a", "a value")
        self.dict.add("b", "b value")
        self.assertEqual("{ 123:value123, 123:value 4, a:a value, b:b value,  }", str(self.dict))

    def test_get_key_from_value(self):
        self.dict.add(123, "value123")
        self.dict.add(123, "value 4")
        self.dict.add("a", "a value")
        self.dict.add("a", "ab value")
        self.assertEqual("a", self.dict.get_key_from_value(value='a value'))