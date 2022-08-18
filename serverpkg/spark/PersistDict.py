import datetime
import sqlite3


def S(a:str) -> str:
    return  '"' + a + '"'


class PersistDict:
    """a dictionary with persistence.
    This is just a glorified dictionary that supports Multi Processs access
    needed because there are several workers, and providing persistence so if the container is
    restarted, the state will not be lost.

    Closing the connection ( by the context manager) causes a commit.
    It is also possible to keep the same connection, and just call commit() where needed."""

    def __init__(self, db_file_name: str, my_name:str):
        self.db_file_name = db_file_name
        self.name = my_name
        self._create_db_table()

    def drop_table(self):
        """cleanup"""
        with sqlite3.connect(self.db_file_name) as conn:
            conn.execute(f"DROP TABLE {self.name}; ")

    @staticmethod
    def _table_schema():
        return  """ "key"     text PRIMARY KEY, \
                    "value"    text, \
                    "update_time" DATETIME \
                  """

    def _create_db_table(self):
        """ the state has to be stored somewhere such as sqlite or redis.
        Verify the table exists"""
        with sqlite3.connect(self.db_file_name) as conn:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {self.name} ( {PersistDict._table_schema()})")

    def add(self, key, value : str):
        """add to the dict. If value already exists, it is overridden.
        Save the current time with the value"""
        with sqlite3.connect(self.db_file_name) as conn:
            try:
                conn.execute(
                    f"INSERT INTO {self.name} VALUES ("
                    f" {S(str(key))},"
                    f" {S(value)},"
                    f" {S(str(datetime.datetime.utcnow()))} )")
            except sqlite3.IntegrityError:
                conn.execute(f"UPDATE  {self.name} SET value = {S(value)} , update_time={S(str(datetime.datetime.utcnow()))}  WHERE key = {key} ;")

    def remove(self,key):
        """
        remove a key-> value from the dict
        :return: number of items removed . Should be 0 or 1
        """
        with sqlite3.connect(self.db_file_name) as conn:
            cur = conn.execute(f"DELETE FROM {self.name} WHERE key=?;", (key,))
        return cur.rowcount

    def get(self, key):
        """ get a value from the dict
        :return {'value': the-value, 'update_time': datetime} OR None"""
        with sqlite3.connect(self.db_file_name) as conn:
            cur = conn.execute(f"SELECT value, update_time FROM {self.name} WHERE key=?",(key,) )
            rows = cur.fetchall()
        if len(rows) == 0:
            return None
        dt_object = datetime.datetime.strptime(rows[0][1], '%Y-%m-%d %H:%M:%S.%f')
        return {'value':rows[0][0], 'update_time': dt_object }

    def __contains__(self, key):
        """implements the  "in" functionality.
        return True iff item in self"""
        return self.get(key) is not None

#
# -----------------------------------------------------------------------
#


class PersistMultiDict:
    """a Multidictionary with persistence.
    This is just a glorified multidictionary that supports Multi Processs access
    needed because there are several workers, and providing persistence so if the container is
    restarted, the state will not be lost.

    if I didnt need the persistence, I would use https://github.com/aio-libs/multidict
    Closing the connection ( by the context manager) causes a commit.
    It is also possible to keep the same connection, and just call commit() where needed."""

    def __init__(self, db_file_name: str, my_name:str):
        self.db_file_name = db_file_name
        self.name = "multi" + my_name
        self._create_db_table()

    def drop_table(self):
        """After this operation, MUST create the table before any other operations"""
        with sqlite3.connect(self.db_file_name) as conn:
            conn.execute(f"DROP TABLE {self.name}; ")

    def clear(self):
        """cleanup"""
        with sqlite3.connect(self.db_file_name) as conn:
            conn.execute(f"DELETE FROM {self.name}; ")


    @staticmethod
    def _table_schema():
        """The key->value can appear any number of times."""
        return  """ "key"     text KEY, \
                    "value"    text, \
                    "update_time" DATETIME \
                  """

    def _create_db_table(self):
        """ the state has to be stored somewhere such as sqlite or redis.
        Verify the table exists"""
        with sqlite3.connect(self.db_file_name) as conn:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {self.name} ( {PersistMultiDict._table_schema()})")

    def add(self, key, value : str):
        """add to the dict.
         A new (k->v) is added regardless of the value of key.
        Save the current time with the value"""
        with sqlite3.connect(self.db_file_name) as conn:
            conn.execute(
                f"INSERT INTO {self.name} VALUES ("
                f" {S(str(key))},"
                f" {S(value)},"
                f" {S(str(datetime.datetime.utcnow()))} )")

    def remove_kv(self,key,value):
        """
        remove a key-> value from the dict
        :return: number of items removed . Should be 0 or 1
        """
        with sqlite3.connect(self.db_file_name) as conn:
            cur = conn.execute(f"DELETE FROM {self.name} WHERE key=? AND value=?;", (key,value))
        return cur.rowcount

    def remove(self, key):
        """
        remove all  key-> value from the dict where k = key
        :return: number of items removed . Should be 0 or 1
        """
        with sqlite3.connect(self.db_file_name) as conn:
            cur = conn.execute(f"DELETE FROM {self.name} WHERE key=?;", (key,))
        return cur.rowcount

    def remove_v(self, value):
        """
        remove all  key-> value from the dict where v=value
        :return: number of items removed
        """
        with sqlite3.connect(self.db_file_name) as conn:
            cur = conn.execute(f"DELETE FROM {self.name} WHERE value=?;", (value,))
        return cur.rowcount

    def get(self, key):
        """ get a list of values from the dict
        :return {'value': [value1, ... ], 'update_time': [datetime1, ... ]} """
        with sqlite3.connect(self.db_file_name) as conn:
            cur = conn.execute(f"SELECT value, update_time FROM {self.name} WHERE key=?",(key,) )
            rows = cur.fetchall()

        #dt_object = datetime.datetime.strptime(rows[0][1], '%Y-%m-%d %H:%M:%S.%f')
        values = [a[0] for a in rows]
        times = [a[1] for a in rows]
        return {'value': values, 'update_time': times}

    def get_key_from_value(self, value : str):
        """:return the key whose value is 'value' or None
        """
        with sqlite3.connect(self.db_file_name) as conn:
            cur = conn.execute(f"SELECT key FROM {self.name} WHERE value = ?", (value,) )
            rows = cur.fetchall()
        if rows == []:
            return None
        return rows[0][0]

    def values(self):
        with sqlite3.connect(self.db_file_name) as conn:
            cur = conn.execute(f"SELECT value FROM {self.name} " )
            rows = cur.fetchall()
        values = [a[0] for a in rows]
        return values

    def __contains__(self, key):
        """implements the  "in" functionality.
        return True iff item in self"""
        return len(self.get(key)['value'] ) > 0

    def __str__(self):
        try:
            res = "{ "
            with sqlite3.connect(self.db_file_name) as conn:
                cur = conn.execute(f"SELECT key, value FROM {self.name}" )
                rows = cur.fetchall()
            for r in rows:
                res += f'{r[0]}:{r[1]}, '
            res += " }"
        except sqlite3.OperationalError as ex:
            return str(ex)
        return res
