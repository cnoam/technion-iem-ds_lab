"""
We want to make sure that only one job is accepted/running for each user.
This is done to keep load acceptable.

The simplest solution (that does not work) is to use a global dictionary
(unique-user-file -> spark-job-id)
It does not work because the dict is stored per process in memory, and the gunicorn
creates 3 workers.

Instead, run a Redis service and use this wrapper class
"""
import redis


class RunningJobs:
    """
    support these operations with multi process access and persistance
    - get all key values
    - get value for key
    - set value for key
    - delete (key,value)
    """
    def __init__(self):
        self.redis = None

    def connect_redis(self, host, port):
        self.redis = redis.Redis(host,port,decode_responses=True, db=0)

    def add(self,key,value):
        self.redis.set(key,value)

    def get(self,key):
        return self.redis.get(key)

    def pop(self,key):
        self.redis.delete(key)

    def keys(self):
        return self.redis.keys()

    def items(self):
        """
        get all the items stored
        :return: list[tuple(k,v)]
        """
        # plain vanila impl
        return {k: self.redis.get(k) for k  in self.redis.keys()}

if __name__ == "__main__":
    r = RunningJobs()
    try:
        r.connect_redis('localhost', port=6379) # can throw
    except  redis.exceptions.ConnectionError:
        print("Redis is not running. \n ")
    r.add(key='one',value='111')
    r.add(key='two', value='222')
    r.add(key='two', value='444222')
    r.add(key='three shall be ', value='3')
    x = r.get('one')
    y = r.get('nothing')
    kk = r.keys()
    li = r.items()
    r.pop(key='one')
    x = r.get('one')
    print( li)
    print("========== json:")
    import json
    print(json.dumps(li), sep='KKK' )
    print("========== pprint:")
    import pprint
    #pp = pprint.PrettyPrinter()
    print(pprint.pformat(li,indent=3, width=20))


